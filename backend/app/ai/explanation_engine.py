def explain_metric(entity: dict, metrics: dict) -> str:
    if metrics.get("betweenness", 0) > 0.15:
        return f"{entity['label']} appears structurally important because it connects otherwise weakly connected groups. This is a network pattern, not a finding of wrongdoing."
    return f"{entity['label']} has {entity.get('connections', 0)} recorded connections in the supplied synthetic dataset. Review the linked evidence before drawing conclusions."
