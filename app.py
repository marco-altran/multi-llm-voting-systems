from dotenv import load_dotenv
from ai.factory import create_ai_processor
import asyncio
from typing import List, Tuple, NamedTuple
import argparse

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
    judge_prompt = f"""Given the question:
{prompt}

What vendor reasoning are more likely to be correct? What is the final answer?
{all_votes}"""
    
    # Use the provided processor as the LLM judge
    judged_vote = await processor.process_async(judge_prompt, None)
    return judged_vote


# Example usage
async def main(prompt: str = None):
    if prompt is None:
        prompt = """how many r's in the word strawberry?
    """

    try:
        with open("./images/coins.png", "rb") as image_file:
            image = image_file.read()
    except:
        image = None
    image = None

    majority_vote, votes = await majority_voting_system_votes(prompt, image)
    print(f"{BLUE}{BOLD}Majority Voting Final Vote:{END}", majority_vote)
    
    # Get the judged vote using the LLM judge
    final_judged_vote = await llm_judge(prompt, image, votes)
    print(f"{GREEN}{BOLD}LLM Judge Final Vote:{END}", final_judged_vote)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run voting system with optional prompt')
    parser.add_argument('--prompt', type=str, help='Input prompt for the voting system')
    args = parser.parse_args()
    
    asyncio.run(main(args.prompt))
