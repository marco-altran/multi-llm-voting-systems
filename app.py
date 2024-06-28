from dotenv import load_dotenv
from ai.factory import create_ai_processor

load_dotenv()

google_processor = create_ai_processor("google", "gemini-1.5-flash-001")
openai_processor = create_ai_processor("openai", "gpt-4o")
anthropic_processor = create_ai_processor(
    "anthropic", "claude-3-5-sonnet-20240620")
voters = [google_processor, openai_processor, anthropic_processor]


def majority_voting_system_votes(prompt, image):
    votes = []
    for voter in voters:
        vote = voter.process(prompt, image)
        votes.append(int(vote) if vote.isdigit() else vote)
        print(
            f"VENDOR: {voter.get_vendor()} MODEL: {voter.get_model_name()} VOTE: {vote}")
    return max(set(votes), key=votes.count)


def weighted_voting_system_votes(prompt, image, weights):
    weighted_responses = {}

    for voter, weight in zip(voters, weights):
        vote = voter.process(prompt, image)
        vote = int(vote) if vote.isdigit() else vote
        print(
            f"VENDOR: {voter.get_vendor()} MODEL: {voter.get_model_name()} VOTE: {vote} WEIGHT: {weight}")
        weighted_responses[vote] = weighted_responses.get(vote, 0) + weight

    return max(weighted_responses, key=weighted_responses.get)


# Example usage
prompt = "How many coins are in the image? Only respond with a number."

with open("./images/coins.png", "rb") as image_file:
    image = image_file.read()

final_vote = majority_voting_system_votes(prompt, image)
print("Majority Voting Final Vote:", final_vote)
# Example weights for Google Gemini, OpenAI GPT-4o, and Claude Sonnet respectively
weights = [0.4, 0.3, 0.3]
final_vote = weighted_voting_system_votes(prompt, image, weights)
print("Weighted Voting Final Vote:", final_vote)
