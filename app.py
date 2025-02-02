from dotenv import load_dotenv
from ai.factory import create_ai_processor
import asyncio
from typing import List, Tuple

load_dotenv()

google_processor = create_ai_processor("google", "gemini-1.5-flash-001")
openai_processor = create_ai_processor("openai", "o3-mini")
o1_processor = create_ai_processor("openai", "o1")
# anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-20240620")
anthropic_processor = create_ai_processor("anthropic", "claude-3-5-sonnet-latest")
voters = [google_processor, openai_processor, anthropic_processor, o1_processor]


async def get_vote(voter, prompt: str, image: bytes) -> Tuple[str, str, str]:
    vote = await voter.process_async(prompt, image)
    vote = int(vote) if vote.isdigit() else vote
    print(
        f"VENDOR: {voter.get_vendor()} MODEL: {voter.get_model_name()} VOTE: {vote}")
    return vote, voter.get_vendor(), voter.get_model_name()


async def majority_voting_system_votes(prompt: str, image: bytes):
    vote_tasks = [get_vote(voter, prompt, image) for voter in voters]
    votes = await asyncio.gather(*vote_tasks)
    
    # Extract just the votes from the results
    vote_values = [vote[0] for vote in votes]
    return max(set(vote_values), key=vote_values.count)


async def weighted_voting_system_votes(prompt: str, image: bytes, weights: List[float]):
    vote_tasks = [get_vote(voter, prompt, image) for voter in voters]
    votes = await asyncio.gather(*vote_tasks)
    
    weighted_responses = {}
    for (vote, vendor, model), weight in zip(votes, weights):
        weighted_responses[vote] = weighted_responses.get(vote, 0) + weight

    return max(weighted_responses, key=weighted_responses.get)


# Example usage
async def main():
    prompt = """how many r's in the word strawberry?
    """

    try:
        with open("./images/coins.png", "rb") as image_file:
            image = image_file.read()
    except:
        image = None
    image = None

    final_vote = await majority_voting_system_votes(prompt, image)
    print("Majority Voting Final Vote:", final_vote)

if __name__ == "__main__":
    asyncio.run(main())
