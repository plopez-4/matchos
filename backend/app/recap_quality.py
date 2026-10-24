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
    # Target known positive interpretations; do not reject factual disclaimers
    # such as "these counts do not establish control or chance quality".
    unsupported = (
        r'\b(?:pressure|pressing|threat|danger|presion|amenaza|peligro)\b',
        # Spanish scoreboard "domina 1-0" means leads; unspecific domination
        # remains an unsupported interpretation checked here and by the reviewer.
        r'\bdomina(?:n)?\b(?!\s+\d+\s*[-:]\s*\d+)',
        r'\b(?:quality|better|high-quality) (?:chances?|opportunities)|\bocasiones? claras?\b',
        r'\b(?:player_shot_creation|player_shooting|player_forward_passing|metric_window|editorial_plan)\b',
        r'\b(?:fine|precise|brilliant|superb) (?:goal|strike|shot|finish)\b',
        r'\b(?:vision|finishing quality|combined seamlessly|seamless (?:combination|partnership))\b',
        r'\b(?:set|sets|setting) the tone\b|\bsharp build[- ]up\b',
        r'\b(?:marco|marca|marcando) el ritmo\b',
        r'\b(?:intense|thrilling|lively|frenetic)\s+(?:(?:first|second|opening|closing)\s+)?(?:half|match|game)\b',
        r'\b(?:(?:primera|segunda)\s+)?(?:mitad|parte|partido)\s+(?:intens[oa]|vibrante|emocionante)\b',
        r'\bbalanced (?:contest|match|game)\b|\bpartido equilibrado\b',
        r'\bmomentum shifts?\b|\bshifts? in momentum\b|\bcambios? de ritmo\b',
        r'\b(?:gol|disparo|remate) (?:preciso|brillante|magistral)|\b(?:vision|se combinaron perfectamente)\b',
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
    groups = {
        r'\b(?:pass(?:es|ing)?|pases?)\b': [fact for fact in facts if fact['fact_id'] == 'passing' or fact['data'].get('kind') in ('progressive_pass', 'player_forward_passing', 'player_shot_creation') or fact['data'].get('metric', {}).get('goal_link')],
        r'\b(?:shots?|attempts?|remates?|tiros?)\b': [fact for fact in facts if fact['fact_id'] == 'shots' or fact['data'].get('kind') in ('shot_activity', 'player_shooting', 'player_shot_creation', 'recovery_shot')],
    }
    for index, sentence in enumerate(sentences):
        for pattern, metrics in groups.items():
            if not re.search(pattern, sentence, re.I):
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
                if (link and point and point not in clause and index+1<len(sentences)
                        and point in sentences[index+1]
                        and any(normalized(name) in normalized(sentence)
                                for name in (link['recoverer'],link.get('team_name','')) if name)):
                    clause=sentences[index+1]
                if point and point not in clause and not re.search(r'\d{1,3}:\d{2}', sentence) and index and re.match(r'^(?:this|these|that|those|esta|este|estos|estas)\b', normalized(sentence)):
                    clause = sentences[index-1]
                return bool(point and point in clause)
            if not any(allowed & contextual_ranges(fact) or point_supported(fact) for fact in metrics):
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

    def named(name, sentence):
        full = normalized(name)
        aliases = {full}
        for part in (full.split()[0], full.split()[-1]):
            if len(part) >= 3 and not any(part in other.split() for other in known_names if other != full):
                aliases.add(part)
        return any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', normalized(sentence)) for alias in aliases)
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
        elif kind == 'shot_activity' and 'current' in metric:
            counts = [metric['current']['shot_count'], metric['previous']['shot_count']]
        elif kind in ('high_recovery', 'progressive_pass', 'recovery_shot'):
            key = {'high_recovery': 'recovery_count', 'progressive_pass': 'pass_count',
                   'recovery_shot': 'elapsed_seconds'}[kind]
            counts = [metric[key]]
            if kind == 'recovery_shot' and metric.get('goal_link'):
                link = metric['goal_link']
                names = [link['recoverer'], link['scorer']]
                connected=[]
                for index,sentence in enumerate(sentences):
                    after=' '.join(sentences[index:index+2])
                    context=' '.join(sentences[max(0,index-1):index+2])
                    plain_context=normalized(context)
                    timed_shot=(link['shot_clock'] in sentence and re.search(
                        r'\b(?:shot|shoots?|fired|remato|disparo|tiro)\b',normalized(sentence))
                        and str(metric['elapsed_seconds']) in count_digits(context))
                    passing_path=(link['recovery_clock'] in context and re.search(r'\b(?:passes|pases)\b',plain_context)
                                  and str(link['completed_pass_count']) in count_digits(context)
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
                            and str(link['completed_pass_count']) not in count_digits(sentence)):
                        raise RecapQualityError('wrong_scoring_sequence_pass_count', fact_id=fact['fact_id'])
                    for claim in re.finditer(r'\b(?:completed|completing|completo|completaron|completando)\s+(\w+)\s+(?:passes|pases)\b',plain):
                        prefix=plain[:claim.start()]
                        actors={row['player_name'] for row in link.get('completed_passes',[])}
                        candidates=[(max(prefix.rfind(normalized(actor)),prefix.rfind(normalized(actor.split()[-1]))),actor)
                                    for actor in actors if named(actor,prefix)]
                        team_position=team_subject_position(prefix,link.get('team_name',''))
                        if candidates:
                            position,actor=max(candidates)
                            actual=sum(row['player_name']==actor for row in link['completed_passes'])
                            if position>team_position and count_digits(claim.group(1))!=[str(actual)]:
                                raise RecapQualityError('wrong_scoring_sequence_pass_credit',fact_id=fact['fact_id'],
                                    player=actor, claimed_count=count_digits(claim.group(1)),
                                    individual_completed_passes=actual,
                                    team_name=link['team_name'], team_completed_passes=link['completed_pass_count'])
                continue  # The linked path has its own measured duration OR verified team-pass count.
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
