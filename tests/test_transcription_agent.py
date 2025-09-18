import textwrap

from dentist_agent.transcription_agent import DentistSOAPAgent


def test_generate_soap_note_basic_classification():
    transcript = textwrap.dedent(
        """
        Patient Jane Doe: I'm having throbbing pain on the lower right molar.
        Dentist Dr. Lee: Observed caries on tooth #31 with mild inflammation.
        Assistant Maya: I'll schedule Jane for a composite filling and provide post-op instructions.
        """
    ).strip()
    agent = DentistSOAPAgent()

    note = agent.generate_soap_note(transcript)

    assert note.patient_name == "Jane Doe"
    assert note.subjective == ["I'm having throbbing pain on the lower right molar."]
    assert note.assessment == ["Observed caries on tooth #31 with mild inflammation."]
    assert note.plan == [
        "I'll schedule Jane for a composite filling and provide post-op instructions."
    ]
    # Objective should remain empty for this short example.
    assert note.objective == []


def test_parse_transcript_handles_multiline_entries():
    transcript = textwrap.dedent(
        """
        Dentist: First line of observation
            continuing on a second line.
        Patient: Thank you doctor.
        """
    ).strip()
    agent = DentistSOAPAgent()

    utterances = agent.parse_transcript(transcript)

    assert len(utterances) == 2
    assert utterances[0].speaker == "Dentist"
    assert (
        utterances[0].text
        == "First line of observation continuing on a second line."
    )
