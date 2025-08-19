import argparse
import time

from main import run_once

SAMPLE_ITEMS = [
    {
        "source": "sample",
        "title": "OpenAI releases cost-effective model for content generation",
        "url": "https://example.com/openai-cheap-model",
    },
    {
        "source": "sample",
        "title": "Microsoft integrates AI agents across developer tools",
        "url": "https://example.com/microsoft-ai-agents",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Run the LinkedIn/X poster immediately (test helper)")
    parser.add_argument("--dry-run", action="store_true", help="Do not post, only print outputs")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to run (default: 1)")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=5,
        help="Seconds to wait between runs when repeating (default: 5)",
    )
    parser.add_argument("--no-reddit", action="store_true", help="Disable Reddit fetching")
    parser.add_argument("--no-x", action="store_true", help="Disable X fetching")
    parser.add_argument(
        "--use-samples",
        action="store_true",
        help="Use built-in sample items to avoid API calls for instant testing",
    )
    args = parser.parse_args()

    override_items = SAMPLE_ITEMS if args.use_samples else None

    for i in range(max(1, args.repeat)):
        print(f"Run {i+1}/{args.repeat} (dry_run={args.dry_run})")
        run_once(
            dry_run=args.dry_run,
            disable_reddit=args.no_reddit,
            disable_x=args.no_x,
            override_items=override_items,
        )
        if i < args.repeat - 1 and args.interval_seconds > 0:
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
