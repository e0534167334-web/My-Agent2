def score(inputs,outputs,reference_outputs):
    return {'key':'policy_correct','score':int(outputs.get('type')==reference_outputs['type'] and outputs.get('reminders')==reference_outputs['reminders'])}
