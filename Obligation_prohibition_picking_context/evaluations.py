from sklearn.metrics import precision_score, recall_score, f1_score
import difflib

def string_match(a, b):
    return a.strip().lower() == b.strip().lower()

def fuzzy_match(a, b, threshold=0.8):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

def evaluate_annotations(generated, ground_truth):
    """
    Compares a list of LLM-generated annotations to the gold standard.
    """
    tp, fp, fn = 0, 0, 0

    matched = []
    for g in generated:
        best_match = None
        best_score = 0

        for gt in ground_truth:
            score = 0
            score += int(string_match(g['type'], gt['type']))
            score += int(string_match(g['for'], gt['for']))
            score += int(fuzzy_match(g['to'], gt['to']))

            matched_conditions = 0
            for cond in g['conditions']:
                for cond_gt in gt['conditions']:
                    if cond['type'] == cond_gt['type'] and fuzzy_match(cond['text'], cond_gt['text']):
                        matched_conditions += 1
                        break

            score += matched_conditions
            if score > best_score:
                best_score = score
                best_match = gt

        if best_score >= 3:
            matched.append((g, best_match))
            tp += 1
        else:
            fp += 1

    fn = len(ground_truth) - tp

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "matched_pairs": matched
    }
import json
with open("outputs/2014_6_part_1.json", "r") as f:
    ground_truth = json.load(f)
with open("outputs/llm_all_sections_output.json", "r") as f:
    annotations = json.load(f)

# Assume you already ran LLM and got annotations
result = evaluate_annotations(generated=annotations, ground_truth=ground_truth)
print(result)
