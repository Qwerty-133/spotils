"""Type-aliases which aren't specific to any modules."""
import typing as t

JSONSimpleVals: t.TypeAlias = t.Union[str, bool, int, float, None]
JSONVals: t.TypeAlias = t.Union[
    JSONSimpleVals, list["JSONVals"], dict[str, "JSONVals"]
]
