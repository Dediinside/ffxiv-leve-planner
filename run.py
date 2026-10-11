"""Run from any working directory: python path/to/run.py."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="FFXIV Tradecraft Leve Planner")
    parser.add_argument("--demo", action="store_true", help="Искусственные цены, без сети")
    parser.add_argument("--refresh", action="store_true", help="Обновить каталог и выйти")
    parser.add_argument("--cli", action="store_true", help="Расчёт в консоли без окна")
    parser.add_argument("--job", default="Carpenter")
    parser.add_argument("--level", type=int, default=20)
    parser.add_argument("--xp", type=int, default=0)
    parser.add_argument("--budget", type=int, default=100000)
    parser.add_argument("--allowances", type=int, default=100)
    parser.add_argument("--scope", default="Light", help="Имя DC или ID/имя мира")
    parser.add_argument("--craft-hq", action="store_true")
    parser.add_argument("--tax", type=float, default=5)
    parser.add_argument("--travel", type=int, default=0)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.refresh:
        from leveplanner.catalog import refresh
        data = refresh(root / "cache" / "catalog.json", print)
        print(f"Обновлено: {len(data['leves'])} leves, {data['metadata']['commit']}")
    elif args.cli:
        from leveplanner.catalog import JOBS, available, load
        from leveplanner.market import Market
        from leveplanner.net import JsonCache
        from leveplanner.planner import Settings, market_ids, recommend
        if args.job not in JOBS:
            parser.error("Профессия: " + ", ".join(JOBS))
        data = load(root / "cache" / "catalog.json" if (root / "cache" / "catalog.json").exists() else root / "data" / "catalog.json")
        scope_options = json.loads((root / "data" / "scopes.json").read_text(encoding="utf-8"))
        world_names = {k.removeprefix("Мир · ") for k in scope_options if k.startswith("Мир · ")}
        if args.scope not in set(scope_options.values()) | world_names:
            parser.error("Неизвестный мир/DC глобального клиента; выберите его в интерфейсе")
        settings = Settings(args.job, args.level, args.xp, args.budget, args.allowances, args.tax, args.craft_hq, args.travel)
        leves = available(data, args.job, args.level)
        ids = market_ids(data, leves, settings)
        if args.demo:
            from leveplanner.app import demo_prices
            prices, warnings = demo_prices(data, ids), ["DEMO: искусственные цены"]
        else:
            market = Market(JsonCache(root / "cache" / "http"))
            prices = market.fetch(args.scope, ids)
            warnings = market.warnings
        plans = recommend(data, leves, prices, settings)
        rows = [{"leve": p.leve["name"], "method": p.method, "quality": p.quality,
                 "accepts": p.progress.accepts, "turnins": p.progress.turnins,
                 "allowances": p.allowances, "cost": p.cost, "reward": p.reward,
                 "expense": -p.cost if p.cost is not None else None,
                 "balance": p.balance, "feasible": p.feasible, "problems": p.problems} for p in plans[:10]]
        print(json.dumps({"warnings": warnings, "plans": rows}, ensure_ascii=False, indent=2))
    else:
        from leveplanner.app import launch
        launch(args.demo)


if __name__ == "__main__":
    main()
