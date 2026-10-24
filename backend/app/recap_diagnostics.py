"""Request-scoped, opt-in local evaluation trace. Never attached to fan responses."""
from contextlib import contextmanager
from contextvars import ContextVar

_CURRENT = ContextVar('recap_evaluation_trace', default=None)


@contextmanager
def capture():
    rows=[]
    token=_CURRENT.set(rows)
    try:
        yield rows
    finally:
        _CURRENT.reset(token)


def record(stage, draft=None, error=None):
    rows=_CURRENT.get()
    if rows is None or len(rows)>=8:
        return
    row={'stage':stage}
    if isinstance(draft,dict):
        row['draft']={lang:draft[lang][:9000] for lang in ('en','es') if isinstance(draft.get(lang),str)}
        row['draft']['fact_ids']=[value[:256] for value in draft.get('fact_ids',[])[:128]
                                 if isinstance(value,str)] if isinstance(draft.get('fact_ids'),list) else []
    if error is not None:
        row['error']=str(error)
        # Only internal validation details; never provider responses or configuration.
        row['details']=error.details
    rows.append(row)
