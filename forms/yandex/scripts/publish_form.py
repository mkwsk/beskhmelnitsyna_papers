from __future__ import annotations

import argparse

from yf_client import YandexFormsClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish or unpublish Yandex Form")
    parser.add_argument("survey_id")
    parser.add_argument("action", choices=["publish", "unpublish"])
    args = parser.parse_args()

    client = YandexFormsClient()
    if args.action == "publish":
        client.publish(args.survey_id)
        print(f"Published {args.survey_id}")
    else:
        client.unpublish(args.survey_id)
        print(f"Unpublished {args.survey_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
