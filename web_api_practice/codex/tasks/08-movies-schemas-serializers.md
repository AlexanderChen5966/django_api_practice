# 08-movies-schemas-serializers.md

## 目標
- 定義統一資料模型（`Movie`, `SearchResult`）
- 定義查詢參數 `MoviesSearchQuery`

## 指令
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/schemas.py
@@
 from dataclasses import dataclass
 from typing import List, Optional

 @dataclass
 class Movie:
     id: str
     title: str
     year: Optional[str] = None
     plot: Optional[str] = None
     poster: Optional[str] = None
     genres: Optional[List[int]] = None
     rating: Optional[float] = None
     source: str = "tmdb"

 @dataclass
 class SearchResult:
     items: List[Movie]
     page: int
     total_pages: int
     total_results: int
     source: str
*** End Patch
EOF

applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/serializers.py
@@
 from rest_framework import serializers

 class MoviesSearchQuery(serializers.Serializer):
     query = serializers.CharField(required=True)
     page = serializers.IntegerField(required=False, min_value=1, default=1)
     provider = serializers.ChoiceField(choices=["tmdb","omdb"], required=False)
     lang = serializers.CharField(required=False, default="zh-TW")
*** End Patch
EOF
```

## 驗收
- 可成功匯入 `Movie`、`SearchResult`
- `MoviesSearchQuery` 缺 `query` 時回傳 400
