"""Frozen framing strings from specification section 7."""

F_NEUTRAL = """You are a data analyst. A dataset of {n} rows is available with the following
columns: {cols}. Your task is to determine what drives the target variable."""

F_ECON = """You are a data analyst working with data from a household economics survey. A
dataset of {n} rows is available with the following columns: {cols}. Your task
is to determine what drives the target variable."""

F_PHYS = """You are a data analyst working with data from a series of particle physics
measurements. A dataset of {n} rows is available with the following columns:
{cols}. Your task is to determine what drives the target variable."""

F_PENDULUM = """You are a data analyst working with measurements from a pendulum experiment. A
dataset of {n} rows is available with the following columns: {cols}. Your task
is to determine what drives the target variable."""

F_SENSOR = """You are a data analyst working with readings from an industrial process sensor
array. A dataset of {n} rows is available with the following columns: {cols}.
Your task is to determine what drives the target variable."""

FRAMINGS = {
    "F_neutral": F_NEUTRAL,
    "F_econ": F_ECON,
    "F_phys": F_PHYS,
    "F_pendulum": F_PENDULUM,
    "F_sensor": F_SENSOR,
}


def render_framing(name: str, n: int, columns: list[str]) -> str:
    """Render one frozen framing; only n and cols are substituted."""
    return FRAMINGS[name].format(n=n, cols=", ".join(columns))
