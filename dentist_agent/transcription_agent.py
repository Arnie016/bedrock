"""Rule-based agent for generating dentist SOAP notes from meeting transcripts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class Utterance:
    """Simple representation of a line within a meeting transcript."""

    speaker: str
    text: str

    def normalized_speaker(self) -> str:
        """Return a lowercase speaker identifier without punctuation."""

        return re.sub(r"[^a-z0-9]+", " ", self.speaker.lower()).strip()


@dataclass
class SOAPNote:
    """Structured representation of a SOAP note."""

    patient_name: Optional[str] = None
    subjective: List[str] = field(default_factory=list)
    objective: List[str] = field(default_factory=list)
    assessment: List[str] = field(default_factory=list)
    plan: List[str] = field(default_factory=list)

    def add(self, section: str, statement: str) -> None:
        """Append a statement to a section, avoiding duplicates."""

        store = getattr(self, section)
        statement = statement.strip()
        if statement and statement not in store:
            store.append(statement)

    def to_dict(self) -> Dict[str, object]:
        """Serialise the note as a dictionary."""

        return {
            "patient_name": self.patient_name,
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
        }

    def to_markdown(self) -> str:
        """Render the note as Markdown."""

        lines: List[str] = ["# SOAP Note"]
        if self.patient_name:
            lines.append(f"**Patient:** {self.patient_name}")
            lines.append("")
        for header, values in (
            ("Subjective", self.subjective),
            ("Objective", self.objective),
            ("Assessment", self.assessment),
            ("Plan", self.plan),
        ):
            lines.append(f"## {header}")
            if values:
                for item in values:
                    lines.append(f"- {item}")
            else:
                lines.append("- _No information captured._")
            lines.append("")
        return "\n".join(lines).strip()


class DentistSOAPAgent:
    """Heuristic agent that maps transcript lines into SOAP sections."""

    patient_aliases: Sequence[str] = (
        "patient",
        "pt",
        "client",
    )
    clinician_aliases: Sequence[str] = (
        "dentist",
        "doctor",
        "dr",
        "hygienist",
        "assistant",
        "da",
        "rdh",
    )

    plan_keywords: Sequence[str] = (
        "schedule",
        "follow up",
        "follow-up",
        "plan",
        "next visit",
        "next time",
        "recommend",
        "will ",
        "prescribe",
        "apply",
        "perform",
    )
    assessment_keywords: Sequence[str] = (
        "assessment",
        "diagnos",
        "decay",
        "caries",
        "periodontal",
        "gingivitis",
        "condition",
        "issue",
        "finding",
        "lesion",
        "inflam",
    )

    objective_keywords: Sequence[str] = (
        "radiograph",
        "x-ray",
        "probe",
        "measurement",
        "score",
        "observ",
        "vitals",
        "chart",
        "pocket",
        "plaque",
        "calculus",
    )

    def parse_transcript(self, transcript: str) -> List[Utterance]:
        """Parse a raw transcript into individual utterances."""

        utterances: List[Utterance] = []
        current: Optional[Utterance] = None
        speaker_pattern = re.compile(r"^\s*([^:]+):\s*(.*)$")

        for line in transcript.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = speaker_pattern.match(stripped)
            if match:
                if current is not None:
                    utterances.append(current)
                speaker, text = match.groups()
                current = Utterance(speaker=speaker.strip(), text=text.strip())
            elif current is not None:
                current.text += " " + stripped
        if current is not None:
            utterances.append(current)
        return utterances

    def _is_patient(self, utterance: Utterance) -> bool:
        speaker = utterance.normalized_speaker()
        for alias in self.patient_aliases:
            if speaker.startswith(alias):
                return True
        return False

    def _is_clinician(self, utterance: Utterance) -> bool:
        speaker = utterance.normalized_speaker()
        for alias in self.clinician_aliases:
            if alias in speaker.split():
                return True
        return False

    def guess_patient_name(self, utterances: Iterable[Utterance]) -> Optional[str]:
        """Attempt to infer the patient name from the transcript."""

        for utterance in utterances:
            # Look for "Patient <Name>" patterns in the speaker field.
            match = re.match(r"patient\s+([A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*)", utterance.speaker, re.I)
            if match:
                return match.group(1)
            # Scan the text for phrases such as "patient Mary Johnson".
            match = re.search(
                r"patient(?:'s)?\s+(?:name\s+is\s+)?([A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*)",
                utterance.text,
                re.I,
            )
            if match:
                return match.group(1)
        return None

    def classify(self, utterance: Utterance) -> str:
        """Classify an utterance into a SOAP section."""

        text_lower = utterance.text.lower()
        if self._is_patient(utterance):
            return "subjective"
        if any(keyword in text_lower for keyword in self.plan_keywords):
            return "plan"
        if any(keyword in text_lower for keyword in self.assessment_keywords):
            return "assessment"
        if self._is_clinician(utterance) or any(
            keyword in text_lower for keyword in self.objective_keywords
        ):
            return "objective"
        # Default to subjective if we cannot categorise.
        return "subjective"

    def generate_soap_note(
        self, transcript: str, *, patient_name: Optional[str] = None
    ) -> SOAPNote:
        """Generate a SOAP note from a transcript string."""

        utterances = self.parse_transcript(transcript)
        note = SOAPNote(patient_name=patient_name or self.guess_patient_name(utterances))
        for utterance in utterances:
            section = self.classify(utterance)
            note.add(section, utterance.text)
        return note


def _load_transcript(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")
    return path.read_text(encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a dentist SOAP note from a meeting transcript.",
    )
    parser.add_argument(
        "transcript_path",
        type=Path,
        help="Path to the transcript text file (Speaker: text per line).",
    )
    parser.add_argument(
        "--patient",
        type=str,
        default=None,
        help="Override the detected patient name.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the SOAP note (default: markdown).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    transcript = _load_transcript(args.transcript_path)
    agent = DentistSOAPAgent()
    note = agent.generate_soap_note(transcript, patient_name=args.patient)

    if args.format == "json":
        print(json.dumps(note.to_dict(), indent=2))
    else:
        print(note.to_markdown())


if __name__ == "__main__":
    main()
