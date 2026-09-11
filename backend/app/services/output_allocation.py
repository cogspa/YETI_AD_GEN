"""Deterministic per-audience concepts and format assignments for exact totals."""


def allocate_outputs(brief):
    formats = [fmt.id for fmt in brief.outputFormats]
    audience_ids = [aud.id for aud in brief.audiences]
    total = brief.generation.exactOutputCount
    if total is None:
        return {aid: [list(formats) for _ in range(brief.generation.conceptsPerAudience)] for aid in audience_ids}
    result = {}
    for index, aid in enumerate(audience_ids):
        count = total // len(audience_ids) + (index < total % len(audience_ids))
        concepts = []
        for local_index in range(count):
            if local_index % len(formats) == 0:
                concepts.append([])
            concepts[-1].append(formats[(local_index + index) % len(formats)])
        result[aid] = concepts
    return result
