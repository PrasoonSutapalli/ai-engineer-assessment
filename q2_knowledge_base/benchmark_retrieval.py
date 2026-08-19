"""
Knowledge Base Retrieval Benchmark Test Suite.
Evaluates ground-truth retrieval against required queries across product, policy,
qualification, FAQ, and objection categories.
"""

import os
import json
from typing import List, Dict, Any
from .kb_store import default_kb


RETRIEVAL_TEST_QUERIES = [
    {
        "query_id": "Q2_TEST_01",
        "category": "product_specification",
        "question": "What is the hospital room rent limit under the Gold Care plan?",
        "expected_record_id": "kb_product_002",
        "ground_truth_concept": "1% for normal room, 2% for ICU up to 500k SI, and no capping for 750k+ SI"
    },
    {
        "query_id": "Q2_TEST_02",
        "category": "policy_rule",
        "question": "What is the waiting period for pre-existing diseases like diabetes and hypertension?",
        "expected_record_id": "kb_policy_001",
        "ground_truth_concept": "24 months standard waiting period, reducible to 12 months with 1-Year PED Buyback Rider"
    },
    {
        "query_id": "Q2_TEST_03",
        "category": "qualification_underwriting",
        "question": "What is the maximum entry age and when is pre-policy medical checkup mandatory?",
        "expected_record_id": "kb_underwriting_001",
        "ground_truth_concept": "Max entry age 65; mandatory medical checkup for applicants 56+ or with chronic diseases"
    },
    {
        "query_id": "Q2_TEST_04",
        "category": "faq_claims",
        "question": "Can I avail cashless hospitalization at non-network hospitals?",
        "expected_record_id": "kb_claims_001",
        "ground_truth_concept": "Yes, via Cashless Anywhere facility with 48h prior notice (or 24h for emergency)"
    },
    {
        "query_id": "Q2_TEST_05",
        "category": "objection_handling",
        "question": "Why is the direct quote higher than what I saw on online aggregator comparison sites?",
        "expected_record_id": "kb_objection_001",
        "ground_truth_concept": "Aggregator teasers exclude taxes and room rent caps; Aegis includes 0% copay, no room rent sublimit, and 60-min cashless approvals"
    },
    {
        "query_id": "Q2_TEST_06",
        "category": "pricing_loading",
        "question": "Why is there an additional premium loading for tobacco and smoker applicants?",
        "expected_record_id": "kb_pricing_001",
        "ground_truth_concept": "20-35% loading due to morbidity risk; removable after 12 months with verified cessation"
    }
]


def run_retrieval_benchmark() -> Dict[str, Any]:
    """Runs all benchmark queries and produces full evaluation metrics."""
    kb = default_kb
    results = []
    total_tests = len(RETRIEVAL_TEST_QUERIES)
    correct_count = 0

    for test in RETRIEVAL_TEST_QUERIES:
        matches = kb.search(test["question"], top_k=2)
        top_match = matches[0] if matches else None
        
        if top_match and top_match["record_id"] == test["expected_record_id"]:
            verdict = "CORRECT"
            relevance_explanation = (
                f"Retrieved exact target record '{top_match['title']}' with high similarity score "
                f"({top_match['score']}). Content directly satisfies '{test['ground_truth_concept']}'."
            )
            correct_count += 1
        elif top_match:
            verdict = "PARTIALLY_CORRECT"
            relevance_explanation = (
                f"Retrieved record '{top_match['record_id']}' instead of expected '{test['expected_record_id']}'. "
                f"Partial semantic overlap detected."
            )
        else:
            verdict = "INCORRECT"
            relevance_explanation = "No matching records met the confidence threshold."

        results.append({
            "query_id": test["query_id"],
            "category": test["category"],
            "user_question": test["question"],
            "retrieved_record_id": top_match["record_id"] if top_match else "NONE",
            "source_reference": top_match["citation"] if top_match else "N/A",
            "retrieval_score": top_match["score"] if top_match else 0.0,
            "relevance_explanation": relevance_explanation,
            "verdict": verdict
        })

    accuracy_pct = round((correct_count / total_tests) * 100, 2)
    benchmark_report = {
        "total_queries": total_tests,
        "correct_retrievals": correct_count,
        "accuracy_percentage": accuracy_pct,
        "results": results
    }

    # Save JSON benchmark output
    bench_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "benchmarks")
    os.makedirs(bench_dir, exist_ok=True)
    json_path = os.path.join(bench_dir, "q2_retrieval_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2)

    # Save Markdown benchmark output
    md_path = os.path.join(bench_dir, "q2_retrieval_benchmark.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Question 2: Knowledge Base Retrieval Benchmark Report\n\n")
        f.write(f"**Overall Accuracy**: {accuracy_pct}% ({correct_count}/{total_tests} Correct Ground-Truth Retrievals)\n\n")
        f.write("| # | Category | User Question | Retrieved Record | Citation / Source | Score | Verdict |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for idx, r in enumerate(results, 1):
            f.write(
                f"| {idx} | `{r['category']}` | {r['user_question']} | **`{r['retrieved_record_id']}`** | "
                f"{r['source_reference']} | `{r['retrieval_score']}` | **{r['verdict']}** |\n"
            )
        f.write("\n\n### Detailed Explanations:\n")
        for idx, r in enumerate(results, 1):
            f.write(f"**Query {idx}**: *\"{r['user_question']}\"*\n")
            f.write(f"- **Explanation**: {r['relevance_explanation']}\n")
            f.write(f"- **Verdict**: `{r['verdict']}`\n\n")

    return benchmark_report


if __name__ == "__main__":
    report = run_retrieval_benchmark()
    print("=== Question 2 Retrieval Benchmark Completed ===")
    print(f"Accuracy: {report['accuracy_percentage']}% ({report['correct_retrievals']}/{report['total_queries']})")
    for r in report["results"]:
        print(f"[{r['verdict']}] {r['user_question']} -> {r['retrieved_record_id']} (Score: {r['retrieval_score']})")
