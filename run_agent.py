from src.agent import create_all_agents

def main():
    """Main function: Start interactive Agent conversation"""
    print("=" * 50)
    print("Multi-Agent System - Direct Run Mode")
    print("=" * 50)

    # Initialize all Agents with memory enabled
    router, chat, meeting = create_all_agents(with_memory=True)

    print("Agents initialized successfully!")
    print("Type 'quit' or 'exit' to quit, type 'clear' to clear memory")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            # Handle exit commands
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break

            # Handle clear memory command
            if user_input.lower() == "clear":
                chat._memory.clear()
                print("Memory cleared")
                continue

            # Step 1: Routing decision - identify user intent
            decision = router.decide(user_input)
            print(f"[Router] Intent: {decision.intent}, Confidence: {decision.confidence}")

            # Step 2: Call the corresponding Agent based on intent
            if decision.intent == "meeting":
                result = meeting.summarize(user_input)
                print(f"\n📋 Meeting Minutes")
                print(f"{'='*50}")
                print(f"**Title**: {result.title}")
                print(f"**Date**: {result.date}")
                print(f"**Attendees**: {', '.join(result.attendees)}")
                print(f"\n## Summary\n{result.summary}")
                print(f"\n## Decisions")
                for i, d in enumerate(result.decisions, 1):
                    print(f"{i}. {d}")
                print(f"\n## Action Items")
                print(f"| Action | Owner | Deadline |")
                print(f"|--------|-------|----------|")
                for item in result.action_items:
                    print(f"| {item.action} | {item.owner} | {item.deadline or 'TBD'} |")
                if result.notes:
                    print(f"\n## Notes\n{result.notes}")
            else:
                # Chat processing
                result = chat.invoke(user_input)
                print(f"\nAI: {result}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()