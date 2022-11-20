"""
Models which represent JSON values from API values.

- Models represent dict values returned by the API.
  JSON values str, int, float, bool, True, False and None is stored
  directly as an attribute.
- JSON dicts are always represented by a Model.
- JSON lists are repesented by a list which can contain simple values
  or other Models (for dicts).

Models only hold data which is used in this application.
"""
import dataclasses
import typing as t
from types import NoneType

JSONSimpleVals = t.Union[str, bool, int, float, None]
JSONVals = t.Union[JSONSimpleVals, list["JSONVals"], dict[str, "JSONVals"]]

ModelableJSON = t.Mapping[str, JSONVals]

AtomicTypes = t.Union[
    t.Type["Model"],
    t.Type[str],
    t.Type[bool],
    t.Type[int],
    t.Type[float],
]
AtomicTypes_T = t.TypeVar("AtomicTypes_T", bound=AtomicTypes)


class Model:
    """
    Mixin for spotify models which wrap API responses.

    This class shouldn't be instantiated.
    The models which inherit this class should be dataclasses.
    The model's dataclass fields are used to load the JSON data.
    """

    __slots__ = ()

    DATA_PATHS: t.ClassVar[t.Mapping[str, str]] = {
        "url": "external_urls.spotify",
    }

    def _resolve_path(self, path: str, data: ModelableJSON) -> JSONVals:
        """
        Access a mapping value from a path in the form of "a.b.c".

        "a.b.c" resolves to data["a"]["b"]["c"].
        """
        for key in path.split("."):
            data = data[key]  # type: ignore
        return t.cast(JSONVals, data)

    @staticmethod
    def _parse_atomic_types(
        target_type: AtomicTypes_T,
        value: JSONVals,
    ) -> AtomicTypes_T:
        """
        Convert the value to simple types and models.

        If the target_type is a model, the value is passed to the model.
        If the target_type is a simple json type, the type of the value
        is checked and TypeError is raised if it's not equal to the
        target type.
        """
        if issubclass(target_type, Model):
            return target_type(value)
        if issubclass(target_type, (str, bool, int, float, NoneType)):
            if type(value) != target_type:
                raise TypeError(
                    f"Expected {target_type}, got {type(value)}: {value}"
                )
            return value

        raise TypeError(f"Invalid type: {target_type}.")

    def _load_field_value(
        self, field: dataclasses.Field, data: ModelableJSON
    ) -> None:
        """
        Load a model's field's value given the response data.

        The field's type-hint is used to convert the value.
        Expected type-hints:
            - simple values: str, bool, int, float
            - model types (Track, Album etc)
            - list[model & simple types]
            - t.Optional[all of the types mentioned above]
        """
        # The path is the field's own name if it's not specified
        path = self.DATA_PATHS.get(field.name, field.name)
        value = self._resolve_path(path, data)

        # Handling Optional types, since they're just Unions
        if t.get_origin(field.type) == t.Union:
            # The actual type of t.Optional[int] is int
            type1, type2 = t.get_args(field.type)
            actual_type = type1 if type1 != NoneType else type2
            if value is not None:
                value = self._parse_atomic_types(actual_type, value)
        elif t.get_origin(field.type) == tuple:
            # The actual type of tuple[int] is int
            actual_type = t.get_args(field.type)[0]
            value = tuple(
                self._parse_atomic_types(actual_type, obj) for obj in value
            )
        else:
            # The model needs to be instantiated with the inner
            # response data
            value = self._parse_atomic_types(field.type, value)

        object.__setattr__(self, field.name, value)

    def __init__(self, data: ModelableJSON) -> None:
        """Load the data for all the fields from the JSON data."""
        for field in dataclasses.fields(self):
            self._load_field_value(field, data)


class PagedModel(Model):
    """Models that have a next page are considered paged."""

    __slots__ = ()

    next: t.Optional[str]


model_dataclass = dataclasses.dataclass(
    slots=True,
    eq=True,
    init=False,
    frozen=True,
)


@model_dataclass
class Album(Model):
    """Abstracts albums returned by the API."""

    name: str


@model_dataclass
class Artist(Model):
    """Abstracts artists returned by the API."""

    name: str


@model_dataclass
class Track(Model):
    """Abstracts tracks returned by the API."""

    name: str
    id: str
    album: Album
    duration_ms: int
    artists: tuple[Artist]

    def formatted_duration(self) -> str:
        """Format the track's duration into M:SS or H:MM:SS."""
        mins, seconds = divmod(self.duration_ms / 1000, 60)
        mins = int(mins)
        seconds = round(seconds)

        hrs, mins = divmod(mins, 60)
        hrs = int(hrs)
        mins = int(mins)

        if hrs:
            return f"{hrs}:{mins:02}:{seconds:02}"
        else:
            return f"{mins}:{seconds:02}"


@model_dataclass
class Device(Model):
    """Abstracts device information returned by the API."""

    id: str


@model_dataclass
class Context(Model):
    """Abstracts context information returned by the API."""

    type: str


@model_dataclass
class PlaybackState(Model):
    """Abstracts playback state information returned by the API."""

    device: Device
    is_playing: bool
    # This item could've been a track or an episode
    # but we won't be fetching this data for episodes.
    currently_playing_type: str
    item: t.Optional[Track]
    context: t.Optional[Context]


@model_dataclass
class PlayedItem(Model):
    """Abstracts played items returned by the API."""

    track: Track
    played_at: str


@model_dataclass
class RecentlyPlayed(Model):
    """Abstracts recently played information returned by the API."""

    items: tuple[PlayedItem]


@model_dataclass
class SavedItem(Model):
    """Abstracts saved items returned by the API."""

    track: Track


@model_dataclass
class SavedTracks(PagedModel):
    """Abstracts saved tracks returned by the API."""

    next: t.Optional[str]
    items: tuple[SavedItem]
    total: int


@model_dataclass
class PlaylistItem(Model):
    """Abstracts playlist items returned by the API."""

    track: Track


@model_dataclass
class PlaylistTracks(PagedModel):
    """Abstracts playlist tracks returned by the API."""

    next: t.Optional[str]
    items: tuple[PlaylistItem]
    total: int


@model_dataclass
class PlaylistDetails(PagedModel):
    """Abstracts playlist details returned by the API."""

    tracks: PlaylistTracks
    snapshot_id: str
