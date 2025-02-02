from dotenv import load_dotenv
from ai.factory import create_ai_processor
import asyncio
from typing import List, Tuple, NamedTuple
import argparse
import json
from collections import defaultdict

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
END = "\033[0m"

class VoteResult(NamedTuple):
    vote: str
    vendor: str
    model: str

load_dotenv()

google_processor = create_ai_processor("google", "gemini-1.5-flash-001")
openai_processor = create_ai_processor("openai", "o3-mini")
o1_processor = create_ai_processor("openai", "o1")
# anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-20240620")
anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-latest")
voters = [google_processor, openai_processor, anthropic_processor, o1_processor]


async def get_vote(voter, prompt: str, image: bytes) -> VoteResult:
    vote = await voter.process_async(prompt, image)
    vote = int(vote) if vote.isdigit() else vote
    print(
        f"{YELLOW}VENDOR:{END} {voter.get_vendor()} {YELLOW}MODEL:{END} {voter.get_model_name()} {YELLOW}VOTE:{END} {vote}")
    return VoteResult(str(vote), voter.get_vendor(), voter.get_model_name())


async def majority_voting_system_votes(prompt: str, image: bytes):
    vote_tasks = [get_vote(voter, prompt, image) for voter in voters]
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
async def llm_judge(prompt: str, image: bytes, votes: List[VoteResult], processor=openai_processor):
    # Format the votes into a string suitable for the judge prompt
    all_votes = "\n".join([f"{vote.vendor} ({vote.model}): {vote.vote}" for vote in votes])
    
    # Build the judge prompt using the provided template
#     judge_prompt = f"""Given the question:
# {prompt}

# What is the final answer? Only return the answer with a single letter, no other text.
# Answer:
# {all_votes}"""
    judge_prompt = f"""Given the question:
{prompt}

What is the final answer? Only return the answer with a single letter, no other text.
Answer:
{all_votes}"""
    
    # Use the provided processor as the LLM judge
    judged_vote = await processor.process_async(judge_prompt, None)
    return judged_vote


async def evaluate_benchmark(eval_data):
    scores = defaultdict(int)
    total = len(eval_data)
    judge_score = 0

    for item in eval_data:
        try:
            prompt = item["prompt"]
            expected_answer = item["answer"]
            
            print(f"\n{BOLD}Question ID: {item['question_id']}{END}")
            print(f"{BLUE}Prompt: {prompt}{END}")
            print(f"{YELLOW}Expected Answer: {expected_answer}{END}\n")

            try:
                majority_vote, votes = await majority_voting_system_votes(prompt, None)
                
                # Score individual votes
                for vote in votes:
                    try:
                        if isinstance(vote.vote, str) and vote.vote.strip().upper() == expected_answer.strip().upper():
                            scores[f"{vote.vendor}_{vote.model}"] += 1
                    except Exception as e:
                        print(f"Error scoring vote from {vote.vendor}_{vote.model}: {e}")
                
                # Get and score judge's vote
                try:
                    final_judged_vote = await llm_judge(prompt, None, votes)
                    if isinstance(final_judged_vote, str) and final_judged_vote.strip().upper() == expected_answer.strip().upper():
                        judge_score += 1
                except Exception as e:
                    print(f"Error getting judge's vote: {e}")
                    final_judged_vote = "Error"

                print(f"{BLUE}{BOLD}Majority Vote:{END}", majority_vote)
                print(f"{GREEN}{BOLD}LLM Judge Vote:{END}", final_judged_vote)
                print(f"{YELLOW}{BOLD}Expected Answer:{END}", expected_answer)
                print("-" * 80)
            
            except Exception as e:
                print(f"Error processing votes for question {item['question_id']}: {e}")
                continue

        except Exception as e:
            print(f"Error processing benchmark item: {e}")
            continue

    # Print final scores
    print(f"\n{BOLD}Final Scores:{END}")
    for model, score in scores.items():
        accuracy = (score / total) * 100
        print(f"{model}: {score}/{total} ({accuracy:.2f}%)")
    
    judge_accuracy = (judge_score / total) * 100
    print(f"LLM Judge: {judge_score}/{total} ({judge_accuracy:.2f}%)")

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
