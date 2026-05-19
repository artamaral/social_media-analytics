import unittest
from pathlib import Path
import sys
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent))

sys.modules.setdefault("requests", MagicMock())

from main import extract_returned_ids, find_missing_video_ids


class MissingVideoIdsTest(unittest.TestCase):
    def test_extract_returned_ids_from_youtube_items(self):
        """
        Valida a extracao dos IDs retornados pela YouTube API.

        Entrada:
        - lista simulada de `items` retornados por `videos.list`

        Saida esperada:
        - lista simples contendo apenas os `id` presentes nos itens retornados
        """
        items = [
            {"id": "BH0gnUODKwI", "statistics": {"viewCount": "10"}},
            {"id": "abc123", "statistics": {"viewCount": "20"}},
        ]

        self.assertEqual(
            extract_returned_ids(items),
            ["BH0gnUODKwI", "abc123"],
        )

    def test_missing_ids_include_only_requested_ids_not_returned(self):
        """
        Valida o caso principal de segregacao.

        Entrada:
        - `requested_ids`: IDs enviados para `videos.list`
        - `returned_ids`: IDs que voltaram na resposta da YouTube API

        Saida esperada:
        - somente IDs solicitados que nao aparecem em `returned_ids`
        """
        requested_ids = ["BH0gnUODKwI", "lFodaSeTE9A", "abc123"]
        returned_ids = ["abc123"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            ["BH0gnUODKwI", "lFodaSeTE9A"],
        )

    def test_returned_ids_are_never_marked_as_missing(self):
        """
        Garante que videos retornados pela API nunca sejam segregados.

        Entrada:
        - todos os IDs solicitados tambem aparecem em `returned_ids`

        Saida esperada:
        - lista vazia, pois nao existe ID ausente
        """
        requested_ids = ["BH0gnUODKwI", "lFodaSeTE9A"]
        returned_ids = ["BH0gnUODKwI", "lFodaSeTE9A"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            [],
        )

    def test_duplicate_requested_ids_are_not_reported_twice(self):
        """
        Garante idempotencia dentro do mesmo lote.

        Entrada:
        - `requested_ids` contem o mesmo ID ausente mais de uma vez
        - `returned_ids` contem apenas o ID saudavel

        Saida esperada:
        - o ID ausente aparece uma unica vez na lista de segregacao
        """
        requested_ids = ["BH0gnUODKwI", "BH0gnUODKwI", "abc123"]
        returned_ids = ["abc123"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            ["BH0gnUODKwI"],
        )

    def test_extra_returned_ids_do_not_create_missing_records(self):
        """
        Protege contra respostas com IDs extras ou inesperados.

        Entrada:
        - `returned_ids` contem todos os solicitados e um ID adicional

        Saida esperada:
        - lista vazia, pois nenhum ID solicitado ficou ausente
        """
        requested_ids = ["abc123"]
        returned_ids = ["abc123", "extra999"]

        self.assertEqual(
            find_missing_video_ids(requested_ids, returned_ids),
            [],
        )


if __name__ == "__main__":
    unittest.main()
