from dotenv import load_dotenv
from ai.factory import create_ai_processor
from ai.openai import OpenAIProcessor
import asyncio
from typing import List, Tuple, NamedTuple
import argparse
import json
from collections import defaultdict
import time

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
END = "\033[0m"

class VoteResult(NamedTuple):
    vote: str
    reasoning: str
    vendor: str
    model: str

load_dotenv()

DEBUG = False

# Number of concurrent benchmark questions to process
CONCURRENT_QUESTIONS = 4

gemini_exp_1206 = create_ai_processor("google", "gemini-exp-1206")
gemini_flash_2_thinking = create_ai_processor("google", "gemini-2.0-flash-thinking-exp-01-21")
gemini_flash_1_5 = create_ai_processor("google", "gemini-1.5-flash")
gpt4o_processor = create_ai_processor("openai", "gpt-4o")
o3_mini_processor = create_ai_processor("openai", "o3-mini")
o1_processor = create_ai_processor("openai", "o1")
# anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-20240620")
anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-latest")
deepseek_r1_processor = create_ai_processor("openrouter", "deepseek/deepseek-r1:nitro")
deepseek_r1_qwen_32b_processor = create_ai_processor("openrouter", "deepseek/deepseek-r1-distill-qwen-32b")
deepseek_r1_llama_70b_processor = create_ai_processor("openrouter", "deepseek/deepseek-r1-distill-llama-70b")
voters = [
    # gemini_exp_1206,
    gemini_flash_2_thinking,
    # gemini_flash_1_5,
    # o3_mini_processor,
    # anthropic_processor,
    # o1_processor,
    # deepseek_r1_processor,
    # deepseek_r1_qwen_32b_processor,
    # deepseek_r1_llama_70b_processor,
    # gpt4o_processor
]
classifier_processor = gpt4o_processor
llm_judge_processor = gemini_flash_2_thinking
# llm_judge_processor = gpt4o_processor


async def get_vote(voter, prompt: str, image: bytes, is_benchmark: bool = False, classifier_processor = classifier_processor, question_id: str = None) -> VoteResult:
    start_time = time.time()
    
    if is_benchmark:
        reasoning = await voter.process_async(prompt, image)
        if DEBUG:
            print(f"{BLUE}VENDOR:{END} {voter.get_vendor()} {BLUE}MODEL:{END} {voter.get_model_name()} {BLUE}REASONING:{END} {reasoning}")
        vote = await classifier_processor.classify_letter_async(prompt, reasoning, image)
    else:
        reasoning = await voter.process_async(prompt, image)
        vote = int(vote) if reasoning.isdigit() else reasoning
    
    elapsed_time = time.time() - start_time
    question_info = f"Q{question_id}" if question_id else ""
    print(
        f"{YELLOW}VENDOR:{END} {voter.get_vendor()} {YELLOW}MODEL:{END} {voter.get_model_name()} {question_info} {YELLOW}VOTE:{END} {vote} {YELLOW}TIME:{END} {elapsed_time:.2f}s")
    return VoteResult(str(vote), str(reasoning), voter.get_vendor(), voter.get_model_name())


async def majority_voting_system_votes(prompt: str, image: bytes, is_benchmark: bool = False, question_id: str = None):
    vote_tasks = [get_vote(voter, prompt, image, is_benchmark, question_id=question_id) for voter in voters]
    votes = await asyncio.gather(*vote_tasks)
    
    # Extract just the votes from the results
    vote_values = [vote.vote for vote in votes]
    return max(set(vote_values), key=vote_values.count), votes


async def weighted_voting_system_votes(prompt: str, image: bytes, weights: List[float]):
    vote_tasks = [get_vote(voter, prompt, image) for voter in voters]
    votes = await asyncio.gather(*vote_tasks)
    
    weighted_responses = {}
    for vote, weight in zip(votes, weights):
        weighted_responses[vote.vote] = weighted_responses.get(vote.vote, 0) + weight

    return max(weighted_responses, key=weighted_responses.get)


# New function: llm_judge

async def llm_judge(prompt: str, image: bytes, votes: List[VoteResult], processor=llm_judge_processor, classifier_processor = classifier_processor):
    # Format the votes into a string suitable for the judge prompt
    all_votes = "\n".join([f"{vote.vendor} ({vote.model}): {vote.reasoning}" for vote in votes])
    
    # Build the judge prompt using the provided template
#     judge_prompt = f"""Given the question:
# {prompt}

# What is the final answer? Only return the answer with a single letter, no other text.
# Answer:
# {all_votes}"""
    judge_prompt = f"""Given the question:
{prompt}

What are the models with the best reasoning? What is the final answer?
{all_votes}"""
    
    # Use the provided processor as the LLM judge
    judged_reasoning = await processor.process_async(judge_prompt, None)
    if DEBUG:
        print(f"{BLUE}JUDGED REASONING:{END} {judged_reasoning}")
    judged_vote = await classifier_processor.classify_letter_async(prompt, judged_reasoning, image)
    return judged_vote


async def process_benchmark_question(item):
    try:
        prompt = item["prompt"]
        expected_answer = item["answer"]
        question_id = item["question_id"]
        
        print(f"\n{BOLD}Processing Question ID: {question_id}{END}")
        if DEBUG:
            print(f"{BLUE}Prompt: {prompt}{END}")
            print(f"{YELLOW}Expected Answer: {expected_answer}{END}\n")

        try:
            majority_vote, votes = await majority_voting_system_votes(prompt, None, is_benchmark=True, question_id=question_id)
            
            # Score individual votes
            question_scores = []
            for vote in votes:
                try:
                    if isinstance(vote.vote, str) and vote.vote.strip().upper() == expected_answer.strip().upper():
                        question_scores.append((f"{vote.vendor}_{vote.model}", 1))
                    else:
                        question_scores.append((f"{vote.vendor}_{vote.model}", 0))
                except Exception as e:
                    print(f"Error scoring vote from {vote.vendor}_{vote.model}: {e}")
            
            # Get and score judge's vote
            try:
                judge_start_time = time.time()
                final_judged_vote = await llm_judge(prompt, None, votes)
                judge_elapsed_time = time.time() - judge_start_time
                judge_correct = 1 if isinstance(final_judged_vote, str) and final_judged_vote.strip().upper() == expected_answer.strip().upper() else 0
            except Exception as e:
                print(f"Error getting judge's vote for question {question_id}: {e}")
                final_judged_vote = "Error"
                judge_elapsed_time = 0
                judge_correct = 0

            print(f"{BOLD}Results for Question {question_id}:{END}")
            print(f"  {BLUE}Majority Vote:{END} {majority_vote}")
            print(f"  {GREEN}LLM Judge Vote:{END} {final_judged_vote} {YELLOW}TIME:{END} {judge_elapsed_time:.2f}s")
            print(f"  {YELLOW}Expected Answer:{END} {expected_answer}")
            print("-" * 80)
            
            return question_scores, judge_correct
        
        except Exception as e:
            print(f"Error processing votes for question {question_id}: {e}")
            return [], 0

    except Exception as e:
        print(f"Error processing benchmark item: {e}")
        return [], 0

async def evaluate_benchmark(eval_data):
    benchmark_start_time = time.time()
    scores = defaultdict(int)
    total = len(eval_data)
    judge_score = 0
    
    # Process questions in batches
    for i in range(0, total, CONCURRENT_QUESTIONS):
        batch = eval_data[i:i + CONCURRENT_QUESTIONS]
        print(f"\n{BOLD}Processing batch {i//CONCURRENT_QUESTIONS + 1}: questions {i+1} to {min(i+CONCURRENT_QUESTIONS, total)} of {total}{END}")
        
        # Create tasks for concurrent processing
        tasks = [process_benchmark_question(item) for item in batch]
        
        # Wait for all questions in the batch to complete
        batch_results = await asyncio.gather(*tasks)
        
        # Update scores from batch results
        for question_scores, judge_result in batch_results:
            for model, score in question_scores:
                scores[model] += score
            judge_score += judge_result
        
        print(f"\n{BOLD}Batch {i//CONCURRENT_QUESTIONS + 1} completed{END}")

    # Print final scores
    print(f"\n{BOLD}Final Scores:{END}")
    for model, score in scores.items():
        accuracy = (score / total) * 100
        print(f"{model}: {score}/{total} ({accuracy:.2f}%)")
    
    judge_accuracy = (judge_score / total) * 100
    print(f"LLM Judge: {judge_score}/{total} ({judge_accuracy:.2f}%)")
    
    total_time = time.time() - benchmark_start_time
    print(f"\n{BOLD}Total Benchmark Time:{END} {total_time:.2f} seconds")

async def main(prompt: str = None, run_benchmark: bool = False):
    if run_benchmark:
        try:
            with open("simple_bench_public.json", "r") as f:
                benchmark_data = json.load(f)
                await evaluate_benchmark(benchmark_data["eval_data"])
                return
        except Exception as e:
            print(f"Error loading benchmark data: {e}")
            return

    if prompt is None:
        prompt = """how many r's in the word strawberry?"""

    try:
        with open("./images/coins.png", "rb") as image_file:
            image = image_file.read()
    except:
        image = None
    image = None

    majority_vote, votes = await majority_voting_system_votes(prompt, image)
    print(f"{BLUE}{BOLD}Majority Voting Final Vote:{END}", majority_vote)
    
    final_judged_vote = await llm_judge(prompt, image, votes)
    print(f"{GREEN}{BOLD}LLM Judge Final Vote:{END}", final_judged_vote)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run voting system with optional prompt')
    parser.add_argument('--prompt', type=str, help='Input prompt for the voting system')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark evaluation')
    args = parser.parse_args()
    
    asyncio.run(main(args.prompt, args.benchmark))
