"""jra DB（keiba_live.db）を読み、win5 Repository へ変換移植する"""

import logging
import sqlite3
from datetime import date

from database.models import Horse, Jockey, Race, RaceResult, Trainer
from etl.normalize import (
    normalize_class,
    normalize_surface,
    split_sex_age,
    venue_code_from_race_id,
)

logger = logging.getLogger(__name__)


class JraImporter:
    """jra DB → win5 DB の一括/差分インポート"""

    def __init__(self, jra_db_path, repository):
        self.jra_db_path = str(jra_db_path)
        self.repo = repository

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.jra_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def import_reference(self, conn) -> None:
        for row in conn.execute("SELECT horse_id, name, sex, birth_year FROM horses"):
            self.repo.upsert_horse(
                Horse(
                    horse_id=row["horse_id"],
                    horse_name=row["name"] or "",
                    sex=row["sex"] or "",
                    birth_year=row["birth_year"] or 0,
                )
            )
        for row in conn.execute("SELECT jockey_id, name FROM jockeys"):
            self.repo.upsert_jockey(
                Jockey(jockey_id=row["jockey_id"], jockey_name=row["name"] or "")
            )
        for row in conn.execute("SELECT trainer_id, name FROM trainers"):
            self.repo.upsert_trainer(
                Trainer(trainer_id=row["trainer_id"], trainer_name=row["name"] or "")
            )

    def import_races(self, conn) -> int:
        count = 0
        sql = (
            "SELECT race_id, date, venue, race_number, name, class, distance, "
            "surface, track_condition, weather, head_count FROM races"
        )
        for row in conn.execute(sql):
            cls_name, cls_code = normalize_class(row["class"] or "")
            self.repo.upsert_race(
                Race(
                    race_id=row["race_id"],
                    race_date=date.fromisoformat(row["date"]),
                    venue_code=venue_code_from_race_id(row["race_id"]),
                    venue_name=row["venue"] or "",
                    race_number=row["race_number"] or 0,
                    race_name=row["name"] or "",
                    surface=normalize_surface(row["surface"] or ""),
                    distance=row["distance"] or 0,
                    track_condition=row["track_condition"] or "",
                    weather=row["weather"] or "",
                    race_class=cls_name,
                    race_class_code=cls_code,
                    num_runners=row["head_count"] or 0,
                )
            )
            count += 1
        return count

    def _name_map(self, conn, table, id_col) -> dict:
        return {
            row[id_col]: (row["name"] or "")
            for row in conn.execute(f"SELECT {id_col}, name FROM {table}")
        }

    def import_results(self, conn) -> int:
        horse_names = self._name_map(conn, "horses", "horse_id")
        jockey_names = self._name_map(conn, "jockeys", "jockey_id")
        trainer_names = self._name_map(conn, "trainers", "trainer_id")

        count = 0
        batch: list[RaceResult] = []
        current_rid = None
        for row in conn.execute("SELECT * FROM results ORDER BY race_id"):
            if current_rid is not None and row["race_id"] != current_rid and batch:
                self.repo.bulk_upsert_race_results(batch)
                batch = []
            current_rid = row["race_id"]
            sex, age = split_sex_age(row["sex_age"] or "")
            batch.append(
                RaceResult(
                    race_id=row["race_id"],
                    horse_id=row["horse_id"],
                    horse_name=horse_names.get(row["horse_id"], ""),
                    finish_position=row["finish_position"],
                    post_position=row["post_position"] or 0,
                    horse_number=row["horse_number"] or 0,
                    sex=sex,
                    age=age,
                    weight_carried=row["weight_carried"] or 0.0,
                    jockey_id=row["jockey_id"] or "",
                    jockey_name=jockey_names.get(row["jockey_id"], ""),
                    trainer_id=row["trainer_id"] or "",
                    trainer_name=trainer_names.get(row["trainer_id"], ""),
                    last_3f=row["last_3f"],
                    horse_weight=row["horse_weight"],
                    weight_change=row["weight_change"],
                    odds=row["odds_win"],
                    popularity=row["popularity"],
                    margin=row["margin"] or "",
                    corner_positions=row["passing"] or "",
                    prize_money=row["prize"] or 0.0,
                )
            )
            count += 1
        if batch:
            self.repo.bulk_upsert_race_results(batch)
        return count

    def run(self) -> dict:
        conn = self._connect()
        try:
            self.import_reference(conn)
            n_races = self.import_races(conn)
            n_results = self.import_results(conn)
        finally:
            conn.close()
        logger.info("Imported races=%d results=%d", n_races, n_results)
        return {"races": n_races, "results": n_results}
