# -*- coding: utf-8 -*-

'''
Various features for the Roster modules.
'''
import re
import fnmatch

from salt.ext import six
import salt.utils.minions

try:
    from salt.utils.data import traverse_dict_and_list
except ImportError:
    from salt.utils import traverse_dict_and_list


def glob(pool, tgt, opts=None):
    '''
    '''
    return {
        minion: pool[minion] for minion in pool.keys() if fnmatch.fnmatch(minion, tgt)
    }


def grain(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', ':')
    tgt_expr = delimiter.join(tgt.split(delimiter)[:-1])
    tgt_val = tgt.split(delimiter)[-1]
    return {
        minion: pool[minion]
        for minion in pool.keys()
        if traverse_dict_and_list(
            pool[minion].get('minion_opts', {}).get('grains', {}),
            tgt_expr,
            delimiter=opts.get('delimiter', ':'),
        )
        == tgt_val
    }


def grain_pcre(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', ':')
    tgt_expr = delimiter.join(tgt.split(delimiter)[:-1])
    tgt_val = tgt.split(delimiter)[-1]
    tgt_rgx = re.compile(tgt_val)
    return {
        minion: pool[minion]
        for minion in pool.keys()
        if tgt_rgx.search(
            traverse_dict_and_list(
                pool[minion].get('minion_opts', {}).get('grains', {}),
                tgt_expr,
                delimiter=opts.get('delimiter', ':'),
            )
        )
    }


def pillar(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', ':')
    tgt_expr = delimiter.join(tgt.split(delimiter)[:-1])
    tgt_val = tgt.split(delimiter)[-1]
    return {
        minion: pool[minion]
        for minion in pool.keys()
        if traverse_dict_and_list(
            pool[minion].get('minion_opts', {}).get('pillar', {}),
            tgt_expr,
            delimiter=opts.get('delimiter', ':'),
        )
        == tgt_val
    }


def pillar_pcre(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', ':')
    tgt_expr = delimiter.join(tgt.split(delimiter)[:-1])
    tgt_val = tgt.split(delimiter)[-1]
    tgt_rgx = re.compile(tgt_val)
    return {
        minion: pool[minion]
        for minion in pool.keys()
        if tgt_rgx.search(
            traverse_dict_and_list(
                pool[minion].get('minion_opts', {}).get('pillar', {}),
                tgt_expr,
                delimiter=opts.get('delimiter', ':'),
            )
        )
    }


def list(pool, tgt, opts=None):
    '''
    '''
    return {minion: pool[minion] for minion in pool.keys() if minion in tgt}


def pcre(pool, tgt, opts=None):
    '''
    '''
    rgx = re.compile(tgt)
    return {minion: pool[minion] for minion in pool.keys() if rgx.search(minion)}


def nodegroup(pool, tgt, opts=None):
    '''
    '''
    nodegroups = opts.get('nodegroup', {})
    # tgt is the name of the nodegroup
    if tgt not in nodegroups:
        return {}
    nodegroup_expr = nodegroups[tgt]
    return compound(pool, nodegroup_expr, opts=opts)


def compound(pool, tgt, opts=None):
    '''
    Execute a compound match on a pool of devices returned by the Roster. The
    Roster module must collect the entire list of devices managed by this Master
    / salt-sproxy instance, and this function helps filtering out the Minions
    that are outside of this target expression.
    This function returns the list of Minions matched by the target expression,
    together with their opts (i.e., extra Grains and Pillar).
    The first argument passed in is ``pool`` which is a dictionary containing
    the total group of devices that can possibly be managed, and their opts.
    '''
    minions = {}
    if not isinstance(tgt, six.string_types) and not isinstance(tgt, (list, tuple)):
        log.error('Compound target received that is neither string, list nor tuple')
        return minions

    log.debug('compound_match: %s ? %s', minion_id, tgt)
    ref = {
        'G': grain,
        'P': grain_pcre,
        'I': pillar,
        'J': pillar_pcre,
        'L': list_,
        'N': nodegroup,
        'E': pcre,
    }

    results = []
    opers = ['and', 'or', 'not', '(', ')']

    if isinstance(tgt, six.string_types):
        words = tgt.split()
    else:
        words = tgt[:]

    while words:
        word = words.pop(0)
        target_info = salt.utils.minions.parse_target(word)

        if word in opers:
            if results:
                if results[-1] == '(' and word in ('and', 'or'):
                    log.error('Invalid beginning operator after "(": %s', word)
                    return {}
                if word == 'not':
                    if not results[-1] in ('and', 'or', '('):
                        results.append('and')
            else:
                # seq start with binary oper, fail
                if word not in ['(', 'not']:
                    log.error('Invalid beginning operator: %s', word)
                    return {}

        elif target_info and target_info['engine']:
            engine = ref.get(target_info['engine'])
            if not engine:
                # If an unknown engine is called at any time, fail out
                log.error(
                    'Unrecognized target engine "%s" for target ' 'expression "%s"',
                    target_info['engine'],
                    word,
                )
                return {}
            pool = engine(pool, target_info['pattern'], opts=opts)

        else:
            pool = engine(pool, word, opts=opts)

    return pool
