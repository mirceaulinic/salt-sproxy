# -*- coding: utf-8 -*-
'''
Various features for the Roster modules.
'''
from __future__ import absolute_import

import re
import fnmatch
import logging

import salt.cache
from salt.ext import six
import salt.utils.minions

import salt.utils.dictupdate
from salt.defaults import DEFAULT_TARGET_DELIM

try:
    from salt.utils.data import subdict_match
except ImportError:
    from salt.utils import subdict_match

log = logging.getLogger(__name__)


def load_cache(pool, __runner__, opts, tgt, tgt_type=None):
    '''
    Load the Pillar and Grain cache, as required, and merge the Roster Grains
    and Pillar into.
    '''
    if opts.get('grains'):
        for device, device_opts in six.iteritems(pool):
            if 'minion_opts' not in device_opts:
                device_opts['minion_opts'] = {}
            if 'grains' not in device_opts['minion_opts']:
                device_opts['minion_opts']['grains'] = {}
            device_opts['minion_opts']['grains'] = salt.utils.dictupdate.merge(
                opts['grains'], device_opts['minion_opts']['grains'], merge_lists=True,
            )
    if tgt_type in ('glob', 'pcre', 'list'):
        # When the target type is glob, pcre, or list, we don't require grains
        # or pillar loaded from the cache, because the targeting won't depend on
        # those.
        return pool
    if not opts.get('use_cached_grains', True) and not opts.get(
        'use_cached_pillar', True
    ):
        return pool
    # NOTE: It wouldn't be feasible to use the cache.grains or cache.pillar
    # Runners as they rely on fetching data from the Master, for Minions that
    # are accepted. What we're doing here is reading straight from the cache.
    log.debug('Loading cached and merging into the Roster data')
    cache = salt.cache.factory(opts)
    cache_pool = cache.list('minions')
    for device in cache_pool:
        if device not in pool:
            log.trace('%s has cache, but is not in the Roster pool', device)
            continue
        if 'minion_opts' not in pool[device]:
            pool[device]['minion_opts'] = {'grains': {}, 'pillar': {}}
        cache_key = 'minions/{}/data'.format(device)
        if opts.get('target_use_cached_grains', True) and tgt_type in (
            'compound',
            'grain',
            'grain_pcre',
            'nodegroup',
        ):
            log.debug('Fetching cached Grains for %s', device)
            cached_grains = cache.fetch(cache_key, 'grains')
            if cached_grains:
                pool[device]['minion_opts']['grains'] = salt.utils.dictupdate.merge(
                    cached_grains,
                    pool[device]['minion_opts'].get('grains', {}),
                    merge_lists=True,
                )
        if opts.get('target_use_cached_pillar', True) and tgt_type in (
            'compound',
            'pillar',
            'pillar_pcre',
            'pillar_target',
            'nodegroup',
        ):
            log.debug('Fetching cached Pillar for %s', device)
            cached_pillar = cache.fetch(cache_key, 'pillar')
            if cached_pillar:
                pool[device]['minion_opts']['pillar'] = salt.utils.dictupdate.merge(
                    cached_pillar,
                    pool[device]['minion_opts'].get('pillar', {}),
                    merge_lists=True,
                )
    log.debug('The device pool with the cached data')
    log.debug(pool)
    return pool


def glob(pool, tgt, opts=None):
    '''
    '''
    log.debug('Glob matching on %s ? %s', pool.items(), tgt)
    return {
        minion: pool[minion] for minion in pool.keys() if fnmatch.fnmatch(minion, tgt)
    }


def grain(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', DEFAULT_TARGET_DELIM)
    log.debug('Grain matching on %s, over %s', tgt, pool)
    ret = {
        minion: pool[minion]
        for minion in pool.keys()
        if subdict_match(
            pool[minion].get('minion_opts', {}).get('grains', {}),
            tgt,
            delimiter=delimiter,
        )
    }
    log.debug('Grain match returned')
    log.debug(ret)
    return ret


def grain_pcre(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', DEFAULT_TARGET_DELIM)
    log.debug('Grain PCRE matching on %s, over %s', tgt, pool)
    ret = {
        minion: pool[minion]
        for minion in pool.keys()
        if subdict_match(
            pool[minion].get('minion_opts', {}).get('grains', {}),
            tgt,
            delimiter=delimiter,
            regex_match=True,
        )
    }
    log.debug('Grain PCRE match returned')
    log.debug(ret)
    return ret


def pillar(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', DEFAULT_TARGET_DELIM)
    log.debug('Pillar matching on %s, over %s', tgt, pool)
    ret = {
        minion: pool[minion]
        for minion in pool.keys()
        if subdict_match(
            pool[minion].get('minion_opts', {}).get('pillar', {}),
            tgt,
            delimiter=delimiter,
        )
    }
    log.debug('Pillar match returned')
    log.debug(ret)
    return ret


def pillar_pcre(pool, tgt, opts=None):
    '''
    '''
    delimiter = opts.get('delimiter', DEFAULT_TARGET_DELIM)
    log.debug('Pillar PCRE matching on %s, over %s', tgt, pool)
    ret = {
        minion: pool[minion]
        for minion in pool.keys()
        if subdict_match(
            pool[minion].get('minion_opts', {}).get('pillar', {}),
            tgt,
            delimiter=delimiter,
            regex_match=True,
        )
    }
    log.debug('Pillar PCRE match returned')
    log.debug(ret)
    return ret


def list_(pool, tgt, opts=None):
    '''
    '''
    log.debug('List matching on %s ? %s', pool.items(), tgt)
    return {minion: pool[minion] for minion in pool.keys() if minion in tgt}


def pcre(pool, tgt, opts=None):
    '''
    '''
    log.debug('PCRE matching on %s ? %s', pool.items(), tgt)
    rgx = re.compile(tgt)
    return {minion: pool[minion] for minion in pool.keys() if rgx.search(minion)}


def nodegroup(pool, tgt, opts=None):
    '''
    '''
    nodegroups = opts.get('nodegroups', {})
    # tgt is the name of the nodegroup
    if tgt not in nodegroups:
        return {}
    nodegroup_expr = nodegroups[tgt]
    return compound(pool, nodegroup_expr, opts=opts)


TGT_FUN = {
    'glob': glob,
    'G': grain,
    'grain': grain,
    'P': grain_pcre,
    'grain_pcre': grain_pcre,
    'I': pillar,
    'pillar': pillar,
    'pillar_target': pillar,
    'J': pillar_pcre,
    'pillar_pcre': pillar_pcre,
    'L': list_,
    'list': list_,
    'N': nodegroup,
    'nodegroup': nodegroup,
    'E': pcre,
    'pcre': pcre,
}


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
                results.append(word)
            else:
                # seq start with binary oper, fail
                if word not in ['(', 'not']:
                    log.error('Invalid beginning operator: %s', word)
                    return {}
                results.append(word)

        elif target_info and target_info['engine']:
            engine = TGT_FUN.get(target_info['engine'])
            if not engine:
                # If an unknown engine is called at any time, fail out
                log.error(
                    'Unrecognized target engine "%s" for target ' 'expression "%s"',
                    target_info['engine'],
                    word,
                )
                return {}
            res = engine(pool, target_info['pattern'], opts=opts)
            results.append(str(set(res.keys())))

        else:
            res = glob(pool, word, opts=opts)
            results.append(str(set(res.keys())))

    log.debug('Collected individual results')
    log.debug(results)

    expr_chunks = []
    parens_count = 0
    universe = set(pool.keys())
    # Building the target list, using set theory operations
    # `X and Y` becomes `X & Y`
    # `X or Y` becomes `X | Y`
    # `X and not Y` becomes `X - Y`
    # `X or not Y` becomes `X | ( U - Y )` where U is the universe, in our case
    #   being the total group of devices possibly being managed by this
    #   salt-sproxy instance.
    #
    # The following iteration goes through the list of results, and replaces the
    # CLI operational words, as per logic described above.
    # TODO: the `and not` operation is fine, but the `or not` might be weak as
    # it introduces another set of parens which may mess up the expression.
    # Below, when evaluating the expression, I've added a block to catch the
    # exception and ask for bug report
    for index, res in enumerate(results):
        if res == 'not':
            res = '{} -'.format(universe)
        if res == 'and':
            if results[index + 1] == 'not':
                res = '-'
                results[index + 1] = ''
            else:
                res = '&'
        elif res == 'or':
            if results[index + 1] == 'not':
                res = '| ( {} -'.format(universe)
                parens_count += 1
                results[index + 1] = ''
            else:
                res = '|'
        expr_chunks.append(res)
    expr_chunks += ')' * parens_count

    match_expr = ' '.join(expr_chunks)
    log.debug('Matching expression: %s', match_expr)
    try:
        matched_minions = eval(match_expr)  # pylint: disable=W0123
    except SyntaxError:
        log.error('Looks like this target expression is failing.')
        if 'or not' in tgt:
            log.error(
                'This may be a salt-sproxy bug, please report at: \n'
                'https://github.com/mirceaulinic/salt-sproxy/issues/new?'
                'labels=bug%2C+pending+triage&template=bug_report.md'
                '&title=Issue%20when%20using%20the%20compound%20target'
            )
        return {}
    log.debug('Matched Minions')
    log.debug(matched_minions)

    return {minion: pool[minion] for minion in matched_minions}


TGT_FUN['compound'] = compound
