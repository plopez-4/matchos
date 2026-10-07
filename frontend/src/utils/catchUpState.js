export const initialCatchUpState = { summary: null, busy: false, error: '', generation: 0 };

export function catchUpReducer(state, action) {
  if (action.type === 'reset') {
    return { ...initialCatchUpState, generation: action.generation };
  }
  if (action.generation !== state.generation) return state;
  switch (action.type) {
    case 'start': return { ...state, busy: true, error: '' };
    case 'success': return { ...state, summary: action.result, busy: false, error: '' };
    case 'failure': return { ...state, busy: false, error: action.error };
    default: return state;
  }
}
