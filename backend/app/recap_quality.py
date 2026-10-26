"""Conservative wording/window checks. These do not prove prose entailment."""
import re
import unicodedata
from app.player_impact import KINDS as PLAYER_KINDS


class RecapQualityError(ValueError):
    def __init__(self, code, **details):
        super().__init__(code)
        self.details = details


def label(start, end):
    return f'{max(0, start)//60}:{max(0, start)%60:02d}–{end//60}:{end%60:02d}'


def windows(fact):
    identifier, data = fact['fact_id'], fact['data']
    if identifier in ('shots', 'passing'):
        window = data['window']
        return [label(window['start_exclusive'], window['end_inclusive'])]
    if data.get('kind') == 'shot_activity':
        return [label(data['metric'][part]['start_second'], data['metric'][part]['end_second'])
                for part in ('previous', 'current')]
    if data.get('kind') in ('high_recovery', 'progressive_pass', *PLAYER_KINDS):
        metric = data['metric']
        return [label(metric['start_second'], metric['end_second'])]
    return []


def normalized(text):
    text = text.replace('–', '-').replace('—', '-')
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()


def team_subject_position(prefix, name):
    """A team in 'Lewis recovered for City and completed' is not the passer.

    This is a conservative guard for known EN/ES forms, not a grammar parser.
    A relative clause ('City, who completed') can explicitly transfer the subject.
    """
    full = normalized(name)
    words = {full, full.split()[-1] if full else '', 'team', 'equipo'} - {''}
    spans = {match.span() for word in words
             for match in re.finditer(r'(?<!\w)'+re.escape(word)+r'(?!\w)', prefix)}
    positions = []
    for start, end in spans:
        if any(left <= start and end <= right and (left,right)!=(start,end) for left,right in spans):
            continue  # Do not reinterpret the City inside 'for Manchester City'.
        object_of_preposition = re.search(r'\b(?:for|of|para|de|del)\s+(?:(?:the|el|la)\s+)?$', prefix[:start])
        relative_subject = re.match(r'\s*,?\s*(?:who|which|que)\b', prefix[end:])
        if not object_of_preposition or relative_subject:
            positions.append(start)
    return max(positions, default=-1)


def count_digits(text):
    """Allow small measured counts in words without prescribing the writer's style."""
    text = re.sub(r'\b\d{1,3}:\d{2}\b', '', normalized(text))
    english = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()
    spanish = 'cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte'.split()
    numbers = {word: str(number) for words in (english, spanish) for number, word in enumerate(words)}
    text = re.sub(r'\b(?:' + '|'.join(numbers) + r')\b', lambda match: numbers[match.group()], text)
    return re.findall(r'\b\d+\b', text)


def clock_ranges(text):
    result = set()
    join = r'\s*(?:[-–—‑−]|to|until|through|and|a|al|hasta|y)\s*(?:(?:el|los|the)\s+)?'
    for a, b, c, d in re.findall(r'(\d{1,3}):(\d{2})' + join + r'(\d{1,3}):(\d{2})', text, re.I):
        result.add((int(a)*60+int(b), int(c)*60+int(d)))
    for a, b in re.findall(r'(?:minutes?|minutos?)\s+(\d{1,3})' + join + r'(\d{1,3})(?![\d:])', text, re.I):
        result.add((int(a)*60, int(b)*60))
    return result


def enumerated_shot_points(sentence, facts, packet):
    """Verify a named, counted outcome list against cited shot events.

    An enumeration of exact event times is not a rolling statistic. Only the
    recognized EN/ES construction gets this exception; other claims keep their
    existing scope checks and model review. Do not infer outcomes from clocks.
    """
    plain=normalized(sentence)
    clock=r'\d{1,3}:\d{2}'
    claim=re.search(
        r'\b(?P<count>\w+)\s+(?:(?:later|additional|further)\s+)?'
        r'(?:(?P<en>saved|blocked|missed)\s+shots?(?:\s+by\s+(?P<en_actor>[^.!?;,:\d]{1,80}?))?|'
        r'remates?\s+(?P<es>detenidos?|bloqueados?|desviados?)(?:\s+de\s+(?P<es_actor>[^.!?;,:\d]{1,80}?))?)\s+'
        r'(?:at|a los)\s+(?P<clocks>'+clock+r'(?:\s*(?:,|and|y)\s*(?:(?:at|a los)\s+)?'+clock+r')+)\b',plain)
    if not claim or not count_digits(claim['count']): return False
    actions={action['shot_event_id']:action for fact in facts
             for action in fact.get('chronology',{}).get('actions',[])}
    names={normalized(row[key]) for row in packet.get('events',[])
           for key in ('player_name','recipient_player_name') if row.get(key)}
    names.update(normalized(action['recipient_player_name']) for action in actions.values())
    prefix=plain[:claim.start()]
    actors=set()
    for name in names:
        surname=name.split()[-1]
        aliases={name}
        if len(surname)>=3 and not any(surname in other.split() for other in names-{name}):
            aliases.add(surname)
        if any(re.search(r'\b'+re.escape(alias)+r"(?:'s)?\s+(?:(?:had|took|recorded|tuvo|registro|realizo)\s+)?$",prefix)
               for alias in aliases) or (claim['en_actor'] or claim['es_actor']) in aliases:
            actors.add(name)
    if len(actors)!=1 or not actions: return False
    actor=next(iter(actors))
    clocks=re.findall(clock,claim['clocks'])
    count=int(count_digits(claim['count'])[0])
    outcome=claim['en'] or {'detenido':'saved','bloqueado':'blocked','desviado':'missed'}[claim['es'].rstrip('s')]
    supported=(count==len(clocks)==len(set(clocks)))
    for point in clocks:
        matching=[action for action in actions.values()
                  if normalized(action['recipient_player_name'])==actor
                  and (action.get('shot_clock') or f"{action['shot_second']//60}:{action['shot_second']%60:02d}")==point]
        supported=supported and len(matching)==1 and matching[0]['shot_outcome']==outcome
    if not supported:
        raise RecapQualityError('wrong_enumerated_shots',player=actor,claimed_count=count,
                                claimed_clocks=clocks,claimed_outcome=outcome)
    # This exception cannot lend scope to a second number, action or window.
    return (count_digits(sentence)==[str(count)] and re.findall(clock,plain)==clocks
            and not re.search(r'\b(?:between|from|entre|desde|last|past|ultimos)\b',plain))


def pass_partition(text, link):
    """Recognize a measured individual pass followed by the remaining team passes.

    Only explicit EN/ES count partitions are supported; unrelated digits, scores
    and clocks cannot supply the team total. This is not a general prose parser.
    """
    plain = normalized(text)
    number = r'(?:\d+|one|two|three|four|five|un|uno|dos|tres|cuatro|cinco|a)'
    first = re.search(r'\b(?:completed|completo|completara|made)\s+('+number+r')\s+(?:completed\s+)?(?:pass|pase)\b', plain)
    reverse = re.search(r'\b('+number+r')\s+(?:completed pass by|pase completado por)\s+([^,;.]+?)\s+(?:and|y)\s+('+number+r')\s+(?:others by teammates|por sus companeros)\b', plain)
    more = re.search(r'\b('+number+r')\s+(?:(?:more|team)\s+)*(?:passes|pases)\s*(?:mas\b)?', plain[first.end():]) if first else None
    if reverse:
        left, right = reverse.group(1), reverse.group(3)
        subject = reverse.group(2)
    elif first and more:
        left, right = first.group(1), more.group(1)
        subject = plain[:first.start()]
        # Require the explicit remainder marker rather than two arbitrary counts.
        if not re.search(r'\b(?:more|mas)\b',more.group()): return False
    else:
        return False
    actors = {row['player_name'] for row in link.get('completed_passes', [])}
    positions = [(max(subject.rfind(normalized(actor)),subject.rfind(normalized(actor.split()[-1]))),actor)
                 for actor in actors if normalized(actor) in subject or re.search(r'\b'+re.escape(normalized(actor.split()[-1]))+r'\b',subject)]
    if not positions: return False
    _, actor = max(positions)
    count = lambda word: 1 if word in ('a','un') else int(count_digits(word)[0])
    individual = sum(row['player_name']==actor for row in link['completed_passes'])
    if count(left)!=individual or count(right)!=link['completed_pass_count']-individual:
        raise RecapQualityError('wrong_scoring_sequence_pass_partition',player=actor,
                                individual_completed_passes=individual,team_completed_passes=link['completed_pass_count'])
    return True


def validate_pass_route_recipients(sentence, facts):
    """Check known direct recipients without confusing a route with one passer."""
    passes=[row for fact in facts for row in fact['data'].get('metric',{}).get('goal_link',{}).get('completed_passes',[])]
    passes.extend({'player_name':row['passer'],'recipient_player_name':row['recipient']}
                  for fact in facts for row in fact.get('ordered_actions',[]) if row['action']=='completed_pass')
    people={row[key] for row in passes for key in ('player_name','recipient_player_name') if row.get(key)}
    if not people: return
    aliases={name:{normalized(name)} for name in people}
    for name in people:
        surname=normalized(name).split()[-1]
        if len(surname)>=3 and not any(surname in normalized(other).split() for other in people-{name}):
            aliases[name].add(surname)
    mentions=lambda name,value:list(re.finditer(r'\b(?:'+'|'.join(re.escape(alias) for alias in aliases[name])+r')\b',value))
    plain=normalized(sentence)
    senders={row['player_name'] for row in passes}
    for claim in re.finditer(r'\b(?:passed|passing|paso|pasando)\s+(?:(?:quickly|rapidly|rapidamente)\s+)?(?:to|a)\s+',plain):
        prefix=plain[:claim.start()]
        candidates=[(match.start(),name) for name in senders for match in mentions(name,prefix)]
        if not candidates: continue
        _,actor=max(candidates)
        tail=re.split(r'\b(?:who|quien|que|before|antes)\b|[.!?;]',plain[claim.end():],maxsplit=1)[0]
        tail=re.split(r'\b(?:and|then|y|luego)\s+(?:(?:the|el)\s+)?(?:ball|balon)\b',tail,maxsplit=1)[0]
        tail=re.split(r'\b(?:continuing through|continued through|continuando por|siguiendo por)\b',tail,maxsplit=1)[0]
        # A following named subject starts a new action, not another recipient.
        for name in people:
            for match in mentions(name,tail):
                if match.start()>0 and re.match(r'\s+(?:(?:then|luego)\s+)?(?:passed|passes|passing|found|connected|delivered|scored|scores|scoring|shot|shoots|took|paso|pasa|pasando|encontro|conecto|entrego|anoto|marco|remato|disparo)\b',tail[match.end():]):
                    tail=tail[:match.start()]
                    break
        recipients={row['recipient_player_name'] for row in passes if row['player_name']==actor}
        wrong={name for name in people-recipients if mentions(name,tail)}
        if wrong:
            raise RecapQualityError('wrong_pass_route_recipient',player=actor,
                                    claimed_recipients=sorted(wrong),recorded_recipients=sorted(recipients))


def scoped_ranges(sentence, fact, now):
    result = clock_ranges(sentence)
    plain = normalized(sentence)
    # Relative current wording is unambiguous only without a competing historical range.
    if not result and now is not None:
        match = re.search(r'\b(?:last|past|ultimos)\s+(five|5|cinco|ten|10|diez)\s+(?:minutes|minutos)\b', plain)
        if match:
            duration = 600 if match.group(1) in ('ten', '10', 'diez') else 300
            result.add((max(0, now-duration), now))
    data = fact['data']
    if data.get('kind') == 'shot_activity':
        current, previous = data.get('metric', {}).get('current'), data.get('metric', {}).get('previous')
        if current and previous and (current['start_second'], current['end_second']) in result:
            if re.search(r'\b(?:previous|preceding)\s+(?:five|5)\s+minutes\b|\b(?:cinco|5)\s+minutos\s+anteriores\b', plain):
                result.add((previous['start_second'], previous['end_second']))
    return result


def validate(text, packet, cited):
    plain = normalized(text)
    recorded_reasons = [normalized(reason) for fact in packet.get('facts', [])
                        if fact['fact_id'] in cited and fact['data'].get('kind') == 'red_card'
                        for reason in (fact['data'].get('reason_text') or {}).values()]
    # Target known positive interpretations; do not reject factual disclaimers
    # such as "these counts do not establish control or chance quality".
    unsupported = (
        r'\b(?:pressure|pressing|threat|danger|presion|amenaza|peligro)\b',
        # Spanish scoreboard "domina 1-0" means leads; unspecific domination
        # remains an unsupported interpretation checked here and by the reviewer.
        r'\bdomina(?:n)?\b(?!\s+\d+\s*[-:]\s*\d+)',
        r'\b(?:quality|better|high-quality) (?:chances?|opportunities)|\bocasiones? claras?\b',
        r'\b(?:player_shot_creation|player_shooting|player_forward_passing|metric_window|editorial_plan)\b',
        r'\b(?:fine|precise|brilliant|superb) (?:goal|strike|shot|finish|pass)\b',
        r'\b(?:vision|finishing quality|combined seamlessly|seamless (?:combination|partnership))\b',
        r'\b(?:set|sets|setting) the tone\b|\bsharp build[- ]up\b',
        r'\b(?:marco|marca|marcando) el ritmo\b',
        r'\b(?:intense|thrilling|lively|frenetic)\s+(?:(?:first|second|opening|closing)\s+)?(?:half|match|game)\b',
        r'\b(?:(?:primera|segunda)\s+)?(?:mitad|parte|partido)\s+(?:intens[oa]|vibrante|emocionante)\b',
        r'\bbalanced (?:(?:first|second|opening|closing) )?(?:contest|match|game|half)\b|\bpartido equilibrado\b',
        r'\btightly contested\b|\b(?:partido|encuentro) (?:muy )?disputado\b',
        r'\btight contest\b|\bduelo cerrado\b',
        r'\btension (?:stays|remains|is) high\b|\b(?:high|rising) tension\b|\btension (?:se mantiene|es|sigue) alta\b',
        r'\bmomentum shifts?\b|\bshifts? in momentum\b|\bcambios? de ritmo\b',
        r'\b(?:gol|disparo|remate|pase) (?:preciso|brillante|magistral)|\b(?:vision|se combinaron perfectamente)\b',
        r'\b(?:assists?|asistencias?|asistio|asistid[oa]s?|asistiendo)\b',
        r'\b(?:headers?|headed shots?|dribbl(?:es?|ing)|take[- ]?ons?|line[- ]breaking|broke (?:the )?lines|beat (?:his|their|the) (?:man|defender))\b',
        r'\b(?:cabezazos?|remates? de cabeza|regates?|rompio las lineas|supero a su (?:rival|defensor))\b',
        r'\b(?:increased?|increasing|greater|heightened|mounting|more)\s+(?:(?:their|the|attacking)\s+)*(?:threat|danger|pressure)\b',
        r'\b(?:dominated?|dominating|dominance|outplayed?|deserved)\b',
        r'\b(?:took|taking|seized|seizing)\s+control\b',
        r'\b(?:aumento|aumentado|aumentada|mayor|mas|creciente)\s+(?:(?:la|su|el)\s+)*(?:amenaza|peligro|presion)\b',
        r'\b(?:domino|dominando|dominio|merecio|merecido)\b',
    )
    for pattern in unsupported:
        for match in re.finditer(pattern, plain):
            # An exact recorded disciplinary explanation may describe danger to
            # an opponent's safety; it is not a claim of attacking threat.
            if any(start <= match.start() < start+len(reason)
                   for reason in recorded_reasons for start in [plain.find(reason)] if start >= 0):
                continue
            prefix = plain[max(0, match.start()-100):match.start()]
            # Explicit limitations are not positive claims of dominance or threat.
            if re.search(r'\b(?:do not|does not|cannot|no)\s+(?:prove|establish|imply|show|demuestran?|indican?|prueban?|significan?|establecen?)\s+(?:[a-z]+\s+){0,7}$|\bsin\s+(?:[a-z]+\s+){0,3}$', prefix):
                continue
            if re.search(r"\b(?:not|never|without|don't|doesn't|cannot|no|sin)\s+(?:(?:prove|proving|proof|evidence|establish|establishing|imply|implying|indicate|indicating|measure|measuring|demuestra|demostrar|mide|medir|implica|implicar|evidencia|prueba|of|de|a|any|necessarily|necesariamente)\s+){0,5}$", prefix):
                continue
            raise RecapQualityError('unsupported_interpretation', wording=match.group())
    if packet.get('editorial_plan') is None:
        return
    # AI context uses elapsed time only. Verified fallback countdowns are rendered separately.
    if re.search(r'\b(?:minutes?|seconds?)\s+(?:left|remaining|to go)\b|\b(?:a falta de|faltan|quedan)\b', plain):
        raise RecapQualityError('ambiguous_match_clock')
    facts = [fact for fact in packet['facts'] if fact['fact_id'] in cited]
    now = next((fact['data'].get('match_second') for fact in packet['facts'] if fact['fact_id'] == 'phase'), None)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    normalized_sentences = [normalized(sentence).strip(' .!?') for sentence in sentences]
    if len(set(normalized_sentences)) != len(normalized_sentences):
        raise RecapQualityError('repeated_explanation')
    for fact in facts:
        relationships = fact.get('chronology', {}).get('goal_relationships', [])
        if not any(relation['later_count'] for relation in relationships):
            continue
        ambiguous = r'\b(?:behind (?:that|this|the) goal|detras de (?:ese|este|el) gol)\b'
        if re.search(ambiguous, plain):
            raise RecapQualityError('goal_pattern_chronology', fact_id=fact['fact_id'])
    for fact in facts:
        for scope in fact.get('window_labels', []):
            expected = next(iter(clock_ranges(scope)))
            if not any(expected in scoped_ranges(sentence, fact, now) for sentence in sentences):
                raise RecapQualityError('missing_metric_window', fact_id=fact['fact_id'], expected_window=scope)
    shot_pattern=r'\b(?:shots?|attempts?|remates?|tiros?)\b'
    groups = {
        r'\b(?:pass(?:es|ing)?|pases?)\b': [fact for fact in facts if fact['fact_id'] == 'passing' or fact['data'].get('kind') in ('progressive_pass', 'player_forward_passing', 'player_shot_creation') or fact['data'].get('metric', {}).get('goal_link')],
        shot_pattern: [fact for fact in facts if fact['fact_id'] == 'shots' or fact['data'].get('kind') in ('shot_activity', 'player_shooting', 'player_shot_creation', 'recovery_shot')],
    }
    for index, sentence in enumerate(sentences):
        validate_pass_route_recipients(sentence,facts)
        verified_shot_list=enumerated_shot_points(sentence,facts,packet)
        for pattern, metrics in groups.items():
            action_wording=re.sub(r'\b(?:match|game|clock)\s+passes\s+(?:the\s+)?\d+(?:st|nd|rd|th)?\s+minutes?\b','',sentence,flags=re.I)
            if not re.search(pattern, action_wording, re.I):
                continue
            # Qualitative connective prose is reviewed against event links; only
            # quantified action claims need a numeric window on that sentence.
            if not count_digits(sentence):
                continue
            # Each statistical sentence must carry a window rather than "this period".
            if packet['editorial_plan'].get('status') == 'no_qualifying_change' and re.search(
                r'no qualifying (?:change|pattern)|no (?:new|meaningful|significant) (?:change|pattern)|no se detect|sin cambios', normalized(sentence)):
                continue
            allowed = {pair for fact in metrics for scope in fact.get('window_labels', []) for pair in clock_ranges(scope)}
            def contextual_ranges(fact):
                explicit = scoped_ranges(sentence, fact, now)
                # A following explanation may refer back to "these passes".
                # Inherit only the immediately preceding, matching window and
                # never overwrite an explicit competing time reference.
                if (not explicit and not re.search(r'\d{1,3}:\d{2}', sentence) and index and re.match(r'^(?:this|these|that|those|his|their|esta|este|estos|estas|esa|ese|esos|esas|sus)\b', normalized(sentence))):
                    return scoped_ranges(sentences[index-1], fact, now)
                return explicit
            def point_supported(fact):
                if fact['data'].get('kind')=='player_shot_creation':
                    # A single recorded pass is an event, not a window-wide passing total.
                    # Keep plural/shot claims under the existing statistical scope checks.
                    if (not re.search(r'\b(?:pass|pase)\b',sentence,re.I)
                            or re.search(r'\b(?:passes|pases|shots?|attempts?|remates?|tiros?)\b',sentence,re.I)):
                        return False
                    metric=fact['data']['metric']
                    plain_sentence=normalized(sentence)
                    mentioned=lambda name: any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',plain_sentence)
                        for alias in (normalized(name),normalized(name).split()[-1]) if alias)
                    actions=fact.get('chronology',{}).get('actions',[])
                    matching=[action for action in actions
                              if (action.get('pass_clock') or label(action['pass_second'],action['pass_second']).split('–')[0]) in sentence
                              and mentioned(action['recipient_player_name'])]
                    # An unnamed passer need not be invented or repeated: the
                    # recipient plus exact clock must identify one cited pass.
                    # Do not grant this exception if another named actor competes.
                    if len(matching)!=1: return False
                    if not mentioned(metric['player_name']):
                        point=matching[0].get('pass_clock') or label(matching[0]['pass_second'],matching[0]['pass_second']).split('–')[0]
                        if not re.search(r'\b(?:a pass|un pase)\s+(?:at|a los|al|a las)\s+'+re.escape(point)+r'\b',plain_sentence):
                            return False
                    allowed_people={normalized(metric['player_name']),normalized(matching[0]['recipient_player_name'])}
                    known={normalized(row[key]) for row in packet.get('events',[])
                           for key in ('player_name','recipient_player_name') if row.get(key)}
                    return not any(mentioned(name) for name in known-allowed_people)
                if fact['data'].get('kind') != 'recovery_shot':
                    return False
                point = fact.get('point_clock')
                clause = sentence
                link = fact['data'].get('metric', {}).get('goal_link')
                if link:
                    second=lambda value:sum(int(part)*factor for part,factor in zip(value.split(':'),(60,1)))
                    bounds=(second(link['recovery_clock']),second(link['goal_clock']))
                    if any(start<bounds[0] or end>bounds[1] for start,end in clock_ranges(sentence)):
                        return False
                    nearby=' '.join(sentences[max(0,index-1):index+2])
                    if link['recovery_clock'] in nearby and link['goal_clock'] in nearby:
                        return True
                    # A bounded continuation may follow the scoreboard sentence.
                    # Require the exact linked clocks, duration and any pass partition.
                    prior=' '.join(sentences[max(0,index-3):index])
                    if (re.match(r'^(?:the|this|la|esta) (?:sequence|secuencia)\b',normalized(sentence))
                            and not re.search(r'\d{1,3}:\d{2}',sentence)
                            and link['recovery_clock'] in prior and link['goal_clock'] in prior
                            and str(fact['data']['metric']['elapsed_seconds']) in count_digits(sentence)
                            and re.search(r'\b(?:seconds?|segundos?)\b',sentence,re.I)
                            and re.search(r'\b(?:recover\w*|recuper\w*)\b',normalized(sentence))
                            and (not re.search(r'\b(?:passes|pases|pass|pase)\b',sentence,re.I)
                                 or pass_partition(sentence,link))):
                        return True
                if (link and point and point not in clause and index+1<len(sentences)
                        and point in sentences[index+1]
                        and any(normalized(name) in normalized(sentence)
                                for name in (link['recoverer'],link.get('team_name','')) if name)):
                    clause=sentences[index+1]
                if point and point not in clause and not re.search(r'\d{1,3}:\d{2}', sentence) and index and re.match(r'^(?:this|these|that|those|esta|este|estos|estas)\b', normalized(sentence)):
                    clause = sentences[index-1]
                return bool(point and point in clause)
            def definition_supported(fact):
                if fact['data'].get('kind')!='recovery_shot': return False
                plain_sentence=normalized(sentence)
                threshold=fact['data']['metric'].get('threshold_seconds')
                elapsed=fact['data']['metric'].get('elapsed_seconds')
                duration=re.search(r'\b(?:lasted|duro)\s+(\w+)\s+(?:seconds?|segundos?)\b',plain_sentence)
                prior=' '.join(sentences[max(0,index-5):index])
                measured=(duration and count_digits(duration.group(1))==[str(elapsed)]
                    and count_digits(sentence)==[str(elapsed),str(threshold)]
                    and re.search(r'\b(?:recovery.to.shot|recuperacion.remate|recuperacion a remate)\b',plain_sentence)
                    and fact.get('action_clocks',{}).get('recovery') is not None
                    and fact['action_clocks']['recovery'] in prior and fact.get('point_clock') in prior)
                return bool(threshold is not None and (count_digits(sentence)==[str(threshold)] or measured)
                    and not re.search(r'\d{1,3}:\d{2}',sentence)
                    and re.search(r'\b(?:threshold|rule|umbral|regla|limite)\b',plain_sentence)
                    and re.search(r'\b(?:seconds?|segundos?)\b',plain_sentence)
                    and re.search(r'\b'+str(threshold)+r'(?:-\s*|\s+)(?:seconds?|segundos?)\b',plain_sentence)
                    and re.search(r'\b(?:within|inside|meets?|cumple|dentro)\b',plain_sentence)
                    and not re.search(r'\b(?:outside|fuera)\b|\b(?:not|no)\s+(?:\w+\s+){0,2}(?:within|inside|meet\w*|cumple)\b',plain_sentence)
                    and fact.get('point_clock') in ' '.join(sentences[:index]))
            if not (pattern==shot_pattern and verified_shot_list) and not any(allowed & contextual_ranges(fact) or point_supported(fact) or definition_supported(fact) for fact in metrics):
                raise RecapQualityError('ambiguous_statistic_window', sentence_index=sentences.index(sentence))


def validate_selected_claims(text, packet):
    """Check required names, digits and scope without prescribing wording.

    These are conservative coverage checks, not semantic proof. A separate model
    review must still check attribution, number meaning and bilingual equivalence.
    """
    if packet.get('editorial_plan') is None:
        return
    sentences = re.split(r'(?<=[.!?])\s+', text)
    required = set(packet.get('required_fact_ids', []))
    if any(fact['data'].get('metric',{}).get('goal_link') for fact in packet['facts'] if fact['fact_id'] in required):
        for sentence in sentences:
            if (not count_digits(sentence) and re.search(
                    r'\b(?:this|the|este|esta)\b.{0,55}\b(?:pattern|sequence|chain|patron|secuencia|jugada)\b.{0,55}\b(?:shows|highlights|demonstrates|muestra|destaca|demuestra)\b', normalized(sentence))):
                raise RecapQualityError('repeated_linked_goal_explanation')
    now = next((fact['data'].get('match_second') for fact in packet['facts'] if fact['fact_id'] == 'phase'), None)
    score = next((fact['data'].get('score') for fact in packet['facts'] if fact['fact_id']=='trajectory'), None)
    if score and score['home']==score['away'] and now is not None:
        current_clock=f'{now//60}:{now%60:02d}'
        for sentence in sentences:
            if current_clock in sentence and re.search(r'\b(?:lead|leads|ahead|gana|va por delante|van por delante)\b', normalized(sentence)):
                raise RecapQualityError('contradictory_current_score')
    known_names = {normalized(row[key]) for row in packet.get('events', [])
                   for key in ('player_name', 'recipient_player_name') if row.get(key)}

    trajectory=next((fact['data'] for fact in packet['facts'] if fact['fact_id']=='trajectory'),{})
    transitions=trajectory.get('transitions',[])
    if transitions:
        clock=lambda row:f"{row['match_second']//60}:{row['match_second']%60:02d}"
        goal_clocks={clock(row) for row in transitions}
        equalizer_clocks={clock(row) for row in transitions if row['type']=='equalization'}
        for sentence in sentences:
            plain=normalized(sentence)
            for claim in re.finditer(r'\b(?:goal|gol)\s+(?:at|a los|al|a las)\s+(\d{1,3}:\d{2})',plain):
                if re.search(r'\bintento de\s+$',plain[:claim.start()]):
                    continue  # "intento de gol" denotes a shot, checked separately below.
                if claim.group(1) not in goal_clocks:
                    raise RecapQualityError('wrong_explicit_goal_clock',claimed_clock=claim.group(1),recorded_goal_clocks=sorted(goal_clocks))
            for claim in re.finditer(r'\b(?:equalized?|levelled?|leveled?|empato|igualo)\b[^.!?;:]{0,70}?\b(?:at|a los|al|a las)\s+(\d{1,3}:\d{2})',plain):
                if claim.group(1) not in equalizer_clocks:
                    raise RecapQualityError('wrong_equalizer_clock',claimed_clock=claim.group(1),recorded_equalizer_clocks=sorted(equalizer_clocks))

    def named(name, sentence):
        full = normalized(name)
        aliases = {full}
        for part in (full.split()[0], full.split()[-1]):
            if len(part) >= 3 and not any(part in other.split() for other in known_names if other != full):
                aliases.add(part)
        return any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', normalized(sentence)) for alias in aliases)
    shot_clocks={f"{event['match_second']//60}:{event['match_second']%60:02d}"
                 for event in packet.get('events',[]) if event.get('type')=='shot'}
    shot_clocks.update(row['shot_clock'] for row in transitions if row.get('shot_clock'))
    for fact in packet['facts']:
        shot_clocks.update(action.get('shot_clock') or f"{action['shot_second']//60}:{action['shot_second']%60:02d}"
                           for action in fact.get('chronology',{}).get('actions',[]))
        link=fact['data'].get('metric',{}).get('goal_link')
        if link: shot_clocks.add(link['shot_clock'])
        if fact['data'].get('kind')=='recovery_shot' and fact.get('point_clock'):
            shot_clocks.add(fact['point_clock'])
    for sentence in sentences:
        plain=normalized(sentence)
        explicit_shot=r'\b(?:goal attempt|intento de gol|shot|remate|tiro|disparo)\s+(?:at|a los|al|a las)\s+(\d{1,3}:\d{2})'
        combined=r'\b(?:shot|remato|disparo)\s+(?:and|y)\s+(?:goal|scored|anoto|marco)\s+(?:at|a los|al|a las)\s+(\d{1,3}:\d{2})'
        for pattern in (explicit_shot,combined):
            for claim in re.finditer(pattern,plain):
                if shot_clocks and claim.group(1) not in shot_clocks:
                    raise RecapQualityError('wrong_explicit_shot_clock',claimed_clock=claim.group(1),recorded_shot_clocks=sorted(shot_clocks))
        for row in transitions:
            if not row.get('scorer') or row.get('goal_clock') not in sentence: continue
            for other in {item['scorer'] for item in transitions if item.get('scorer')}-{row['scorer']}:
                person=re.escape(normalized(other))
                at=re.escape(row['goal_clock'])
                before=r'\b'+person+r'\s+(?:scored|marco|anoto)\b[^\d.!?;]{0,65}'+at
                after=at+r'[^\d.!?;]{0,40}?(?:(?:with|con)\s+(?:a goal (?:from|by)|un gol de)\s+'+person+r'\b|with\s+'+person+r'\s+scoring\b)'
                if re.search(before,plain) or re.search(after,plain):
                    raise RecapQualityError('wrong_explicit_goal_scorer',claimed_scorer=other,
                                            recorded_scorer=row['scorer'],goal_clock=row['goal_clock'])
    for fact in packet['facts']:
        if fact['fact_id'] not in required:
            continue
        data = fact['data']
        goal = data.get('goal')
        if goal:
            if not any(named(goal['player_name'], sentence)
                       and goal['clock'] in sentence for sentence in sentences):
                raise RecapQualityError('missing_selected_goal', fact_id=fact['fact_id'],
                                        required_scorer=goal['player_name'], required_goal_clock=goal['clock'],
                                        required_scope='scorer_and_goal_clock_in_same_sentence')
        if data.get('kind') == 'red_card':
            card_terms = r'\b(?:red card|sent off|sending-off|tarjeta roja|expulsad[oa]|expulsion)\b'
            card_explained = any(
                named(data['player_name'], sentence)
                and data['clock'] in sentence
                and re.search(card_terms, normalized(sentence))
                for sentence in sentences
            )
            if not card_explained:
                raise RecapQualityError('missing_selected_red_card', fact_id=fact['fact_id'],
                                        required_player=data['player_name'], required_clock=data['clock'],
                                        required_scope='player_and_card_clock_in_same_sentence')
            if data.get('card_phase') == 'post_match':
                card_sentences = [normalized(s) for s in sentences if named(data['player_name'], s) and data['clock'] in s]
                if not any(re.search(r'after (?:the )?(?:final whistle|full[ -]time)|post[ -]match|despues del (?:pitido|silbatazo) final|tras el pitido final', s) for s in card_sentences):
                    raise RecapQualityError('missing_post_match_card_phase', fact_id=fact['fact_id'])
                if any(re.search(r'down to|played with|reduced to|jugo con|juega con|quedo con', s) for s in card_sentences):
                    raise RecapQualityError('post_match_card_changed_playing_numbers', fact_id=fact['fact_id'])
        metric = data.get('metric', {})
        kind = data.get('kind')
        counts = []
        names = []
        if kind in PLAYER_KINDS:
            counts = [metric['count']]
            names = [metric['player_name']]
            if kind == 'player_shot_creation':
                targets = {link['recipient_player_name'] for link in metric['links']}
                if len(targets) == 1:
                    names.extend(targets)
                for sentence in sentences:
                    if not named(metric['player_name'],sentence): continue
                    for claim in re.finditer(r'\b(?:pass|pase)\b(?P<tail>[^,.!?;:]{0,110}?)\b(?:at|a los|al|a las)\s+(?P<clock>\d{1,3}:\d{2})',normalized(sentence)):
                        if re.search(r'\b(?:scored|marco|anoto|shot|shoots?|remat\w*|dispar\w*|goal|gol)\b',claim['tail']):
                            continue
                        recipients={target for target in targets if named(target,sentence)}
                        if not recipients: continue
                        clocks={action.get('pass_clock') or f"{action['pass_second']//60}:{action['pass_second']%60:02d}"
                                for action in fact.get('chronology',{}).get('actions',[])
                                if action['recipient_player_name'] in recipients}
                        if clocks and claim['clock'] not in clocks:
                            raise RecapQualityError('wrong_creation_pass_clock',fact_id=fact['fact_id'],
                                player=metric['player_name'],claimed_clock=claim['clock'],recorded_pass_clocks=sorted(clocks))
        elif kind == 'shot_activity' and 'current' in metric:
            counts = [metric['current']['shot_count'], metric['previous']['shot_count']]
        elif kind in ('high_recovery', 'progressive_pass', 'recovery_shot'):
            key = {'high_recovery': 'recovery_count', 'progressive_pass': 'pass_count',
                   'recovery_shot': 'elapsed_seconds'}[kind]
            counts = [metric[key]]
            if kind == 'recovery_shot' and not metric.get('goal_link'):
                point=fact.get('point_clock')
                if point and metric.get('elapsed_seconds',0)>0:
                    shot_second=sum(int(part)*factor for part,factor in zip(point.split(':'),(60,1)))
                    recovery_second=shot_second-metric['elapsed_seconds']
                    recovery_clock=f'{recovery_second//60}:{recovery_second%60:02d}'
                    for sentence in sentences:
                        plain=normalized(sentence)
                        for match in re.finditer(re.escape(point),plain):
                            # A leading shot clock must not grammatically introduce a recovery.
                            tail=re.split(r'\d{1,3}:\d{2}',plain[match.end():],maxsplit=1)[0][:140]
                            verb=re.search(r'\b(?:recover\w*|recuper\w*)\b',tail)
                            if verb:
                                before=tail[:verb.start()]
                                after=tail[verb.end():]
                                relative=re.search(r'\b(?:after|following|tras|despues|desde|earlier|antes)\b',before)
                                earlier=re.search(r'\b(?:seconds? earlier|segundos? antes)\b',after)
                                prior_shot=re.search(r'\b(?:shot|shoots?|fired|remat\w*|dispar\w*)\b',before)
                                if not (relative or earlier or prior_shot):
                                    raise RecapQualityError('wrong_recovery_clock',fact_id=fact['fact_id'],
                                        recovery_clock=recovery_clock,shot_clock=point,
                                        participants=fact.get('participants',{}))
                            prefix=re.split(r'[.!?;]',plain[:match.start()])[-1][-140:]
                            verbs=list(re.finditer(r'\b(?:recover\w*|recuper\w*)\b',prefix))
                            if verbs:
                                between=prefix[verbs[-1].end():]
                                if not re.search(r'\b(?:after|before|despues|antes|shot|shoots?|remato|disparo)\b|\d{1,3}:\d{2}',between):
                                    raise RecapQualityError('wrong_recovery_clock',fact_id=fact['fact_id'],
                                        recovery_clock=recovery_clock,shot_clock=point,
                                        participants=fact.get('participants',{}))
            if kind == 'recovery_shot' and metric.get('goal_link'):
                link = metric['goal_link']
                names = [link['recoverer'], link['scorer']]
                connected=[]
                for index,sentence in enumerate(sentences):
                    after=' '.join(sentences[index:index+2])
                    context=' '.join(sentences[max(0,index-1):index+2])
                    plain_context=normalized(context)
                    partition=pass_partition(context,link)
                    timed_shot=(link['shot_clock'] in sentence and re.search(
                        r'\b(?:shot|shoots?|fired|remato|disparo|tiro)\b',normalized(sentence))
                        and str(metric['elapsed_seconds']) in count_digits(context))
                    passing_path=(link['recovery_clock'] in context and re.search(r'\b(?:passes|pases)\b',plain_context)
                                  and (str(link['completed_pass_count']) in count_digits(context) or partition)
                                  and re.search(r'\b(?:recover\w*|recuper\w*)\b',plain_context))
                    if (link['goal_clock'] in after and all(named(name,context) for name in names)
                            and (timed_shot or passing_path)):
                        connected.append(context)
                effects = {'equalization':r'equaliz|level|tie[ds]?|empat|igual',
                           'lead_acquisition':r'lead|ahead|adelant|ventaja|delante',
                           'lead_reversal':r'lead|ahead|adelant|ventaja|delante',
                           'lead_extension':r'extend|increase|ampli|aument',
                           'deficit_reduction':r'deficit|reduce|back|recort|desventaj'}
                if not any(re.search(effects[link['score_change']], normalized(sentence)) for sentence in connected):
                    raise RecapQualityError('missing_recovery_goal_connection', fact_id=fact['fact_id'],
                        recoverer=link['recoverer'], scorer=link['scorer'], recovery_clock=link['recovery_clock'],
                        shot_clock=link['shot_clock'], goal_clock=link['goal_clock'],
                        team_completed_passes=link['completed_pass_count'], seconds_recovery_to_shot=metric['elapsed_seconds'],
                        required_score_change=link['score_change'])
                for sentence in connected:
                    plain=normalized(sentence)
                    for clock_match in re.finditer(re.escape(link['shot_clock']),plain):
                        after=plain[clock_match.end():]
                        recovery_verb=re.search(r'\b(?:recover\w*|recuper\w*)\b',after)
                        if recovery_verb:
                            between=after[:recovery_verb.start()]
                            if (len(between)<100 and not re.search(r'after|despues|desde|\d+:\d+',between)
                                    and named(link['recoverer'],between)):
                                raise RecapQualityError('wrong_recovery_clock',fact_id=fact['fact_id'])
                    if (re.search(r'\b(?:passes|pases)\b', normalized(sentence))
                            and str(link['completed_pass_count']) not in count_digits(sentence)
                            and not pass_partition(sentence,link)):
                        raise RecapQualityError('wrong_scoring_sequence_pass_count', fact_id=fact['fact_id'])
                    for claim in re.finditer(r'\b(?:completed|completing|completes?|completo|completaron|completando|completar)\s+(\w+)\s+(?:team\s+)?(?:passes|pases)\b',plain):
                        # "Three completed team passes" does not mean a player "completed team passes" numerically.
                        claimed=count_digits(claim.group(1))
                        if not claimed:
                            continue
                        prefix=plain[:claim.start()]
                        actors={row['player_name'] for row in link.get('completed_passes',[])}
                        candidates=[(max(prefix.rfind(normalized(actor)),prefix.rfind(normalized(actor.split()[-1]))),actor)
                                    for actor in actors if named(actor,prefix)]
                        team_position=team_subject_position(prefix,link.get('team_name',''))
                        if candidates:
                            position,actor=max(candidates)
                            actual=sum(row['player_name']==actor for row in link['completed_passes'])
                            # An explicit plural subject can own the remaining passes jointly.
                            # "Ugarte and Fernandes completed two" is not Fernandes alone.
                            joint={actor}
                            for other in actors-{actor}:
                                aliases=lambda name:(normalized(name),normalized(name.split()[-1]))
                                if any(re.search(r'\b'+re.escape(a)+r'\s+(?:and|y)\s+'+re.escape(b)+r'\s+(?:then\s+)?$',prefix)
                                       for left,right in ((other,actor),(actor,other))
                                       for a in aliases(left) for b in aliases(right)):
                                    joint.add(other)
                            if len(joint)>1:
                                actual=sum(row['player_name'] in joint for row in link['completed_passes'])
                            if position>team_position and count_digits(claim.group(1))!=[str(actual)]:
                                raise RecapQualityError('wrong_scoring_sequence_pass_credit',fact_id=fact['fact_id'],
                                    player=actor, claimed_count=count_digits(claim.group(1)),
                                    individual_completed_passes=actual,
                                    team_name=link['team_name'], team_completed_passes=link['completed_pass_count'])
                            if position>team_position:
                                recipients={row['recipient_player_name'] for row in link['completed_passes'] if row['player_name'] in joint}
                                clause=re.split(r'\b(?:before|while|mientras|antes|ending|finalizando|who|quien|then|despues)\b',
                                                plain[claim.end():],maxsplit=1)[0]
                                if re.search(r'\b(?:to|a)\b',clause):
                                    known={row[key] for row in link['completed_passes']
                                           for key in ('player_name','recipient_player_name')}
                                    unsupported={target for target in known if named(target,clause) and target not in recipients}
                                    if unsupported:
                                        raise RecapQualityError('wrong_scoring_sequence_pass_recipient',fact_id=fact['fact_id'],
                                            player=actor,claimed_recipients=sorted(unsupported),
                                            recorded_recipients=sorted(recipients))
                continue  # The linked path has its own measured duration OR verified team-pass count.
            if kind=='recovery_shot' and not metric.get('goal_link') and fact.get('point_clock'):
                point=fact['point_clock']
                shot_second=sum(int(part)*factor for part,factor in zip(point.split(':'),(60,1)))
                recovery_second=shot_second-metric['elapsed_seconds']
                recovery_clock=f'{recovery_second//60}:{recovery_second%60:02d}'
                participants=list(fact.get('participants',{}).values())
                # A fully timestamped recorded route can span several short sentences.
                # Every source action, participant and clock must appear in order.
                actions=fact.get('ordered_actions',[])
                for start in range(len(sentences)):
                    context=normalized(' '.join(sentences[start:start+5]))
                    positions=[context.find(action['clock']) for action in actions]
                    if (actions and all(position>=0 for position in positions)
                            and positions==sorted(set(positions))
                            and not set(count_digits(re.sub(r'\b\d+\s*-\s*\d+\b','',context)))-{str(metric['threshold_seconds']),str(metric['elapsed_seconds'])}):
                        for index,action in enumerate(actions):
                            left=positions[index-1] if index else 0
                            if index:
                                left=context.rfind('.',0,positions[index-1])+1
                            right=positions[index+1] if index+1<len(actions) else len(context)
                            local=context[left:right]
                            names_in_action=[action[key] for key in ('player','passer','recipient') if action.get(key)]
                            if not all(named(name,local) for name in names_in_action): break
                        else:
                            break
                else:
                    actions=[]
                if actions: continue
                # Both exact source clocks express the measured duration without a repeated number.
                if any(recovery_clock in context and point in context
                       and re.search(r'\b(?:recover\w*|recuper\w*)\b',normalized(context))
                       and re.search(r'\b(?:shot|shoots?|fired|remat\w*|dispar\w*|tiros?)\b',normalized(context))
                       and all(named(name,context) for name in participants)
                       for index in range(len(sentences))
                       for context in [' '.join(sentences[index:index+2])]):
                    continue
        if not counts:
            continue
        scopes = {pair for scope in fact.get('window_labels', []) for pair in clock_ranges(scope)}
        candidates = [sentence for index, sentence in enumerate(sentences)
                      if all(named(name, ' '.join(sentences[max(0, index-1):index+1])) for name in names)
                      and (not fact.get('point_clock') or fact['point_clock'] in sentence)
                      and (not scopes or scopes & scoped_ranges(sentence, fact, now))]
        # Clock digits cannot stand in for a measured action count.
        if not any(all(str(count) in count_digits(sentence)
                       for count in counts) for sentence in candidates):
            raise RecapQualityError('missing_selected_contribution', fact_id=fact['fact_id'],
                                    named_scope_found=bool(candidates),
                                    count_found=any(all(str(count) in count_digits(sentence) for count in counts)
                                                    for sentence in sentences))
        if kind == 'player_shot_creation' and len(names) == 2:
            paired = [sentence for sentence in sentences if all(named(name, sentence) for name in names)]
            if len(paired) > 1:
                for sentence in paired:
                    # A second sentence can add an outcome, timing or limit;
                    # simply renaming the same combination adds no information.
                    if (not count_digits(sentence) and not clock_ranges(sentence)
                            and not re.search(r'\b(?:goal|scored|saved|blocked|missed|not|cannot|gol|marco|ataj\w*|parad\w*|bloque\w*|no|sin)\b', normalized(sentence))):
                        raise RecapQualityError('repeated_player_contribution', fact_id=fact['fact_id'])
