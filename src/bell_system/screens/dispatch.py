"""
The command dispatch table and the aliases that reach it.

Two hundred and some commands and their shorthands, kept apart from the
terminal because a table of names is reference data rather than behaviour,
and because terminal.py is meant to stay small enough to read.
"""

from typing import TYPE_CHECKING, Any, Dict


class CommandDispatch:
    """
    What the terminal can run, and what people type instead.

    Mixed into :class:`~bell_system.terminal.BellSystemTerminal`, whose bound
    methods the table refers to.
    """

    if TYPE_CHECKING:  # pragma: no cover
        def __getattr__(self, name: str) -> Any:
            """
            Every command method lives on a sibling mixin.

            The table names a hundred and thirty of them and declaring each
            here would be a second copy of the same list, kept in step by
            hand. The integrity suite already checks that every self.x() call
            resolves against the constructed class, which is the check that
            actually matters.
            """
            ...

    # Enhanced command aliases for improved user experience
    COMMAND_ALIASES = {
        # Traditional UNIX aliases
        'h': 'help',
        '?': 'help',
        'q': 'quit',
        'exit': 'quit',
        'logout': 'quit',
        'clear': 'clear',

        # Bell System operation aliases
        'st': 'status',
        'stat': 'status',
        'tst': 'test',
        'chk': 'test',
        'alm': 'alarm',
        'alert': 'alarm',
        'options': 'set',
        'settings': 'set',
        'config': 'set',

        # Repair service bureau
        'rsb': 'report',
        'board': 'report',
        'reports': 'report',
        'career': 'qual',
        'index': 'qual',
        'ow': 'orderwire',
        'tl': 'testline',
        'tc': 'testcall',
        'call': 'testcall',
        'loop': 'mlt',

        # Technical system aliases
        'rad': 'radio',
        'mw': 'microwave',
        't1': 't1carrier',
        'ds1': 't1carrier',
        'lc': 'lcarrier',
        'coax': 'lcarrier',
        'mult': 'multiplex',
        'mux': 'multiplex',
        'regen': 'regenerator',
        'reg': 'regenerator',

        # Directory and file aliases
        'll': 'ls',
        'la': 'ls',
        'dir': 'ls',

        # System monitoring aliases
        'proc': 'ps',
        'users': 'who',
        'w': 'who',
        'disk': 'df',

        # Bell System specific shortcuts
        'bsp': 'bsp',
        'practices': 'bsp',
        'tnds': 'tnds',
        'sarts': 'sarts',
        'tsps': 'tsps',
        'toll': 'toll',
        'trace': 'trace',
        'route': 'routing',
        'cap': 'capacity',
        'traf': 'traffic',
        'bill': 'billing',
        'cust': 'custdb',
        'db': 'dbquery',
        'net': 'netplan',
        'switch': 'switch',
        'trunk': 'trunk',
        'crossbar': 'crossbar',
        'events': 'events',
        'handoff': 'handoff',
        'tariff': 'tariff',
        'train': 'training',
        '5ess': '5ess',
        'western': 'western',
        'coer': 'coer',
        'lmos': 'lmos'
    }

    def _build_command_handlers(self) -> Dict[str, Any]:
        """
        Build the command name to handler-method dispatch table.

        Called once during initialisation; the resulting table is reused for
        every command rather than being rebuilt on each keystroke.

        Returns:
            Mapping of command name to the bound method implementing it
        """
        return {
        # Core Bell System commands
        'trunk': self.cmd_trunk,
        'switch': self.cmd_switch,
        'testboard': self.cmd_testboard,
        'toll': self.cmd_toll,
        'trace': self.cmd_trace,
        'dialtone': self.cmd_dialtone,
        'emergency': self.cmd_emergency,
        'ticket': self.cmd_ticket,
        'trouble': self.cmd_trouble,
        'uucp': self.cmd_uucp,
        'traffic': self.cmd_traffic,
        'routing': self.cmd_routing,
        'capacity': self.cmd_capacity,
        'weather': self.cmd_weather,
        'force': self.cmd_force,
        'connect': self.cmd_connect,
        'company': self.cmd_company,
        'tone': self.cmd_tone,
        'era': self.cmd_era,
        'billing': self.cmd_billing,
        'service': self.cmd_service,
        'operator': self.cmd_operator,
        'directory': self.cmd_directory,
        'crossbar': self.cmd_crossbar,
        'netplan': self.cmd_netplan,
        'dbquery': self.cmd_dbquery,
        'custdb': self.cmd_custdb,
        'provision': self.cmd_provision,
        'collect': self.cmd_collect,
        'tsps': self.cmd_tsps,
        'handoff': self.cmd_handoff,
        'shift': self.cmd_shift,
        'tariff': self.cmd_tariff,
        'events': self.cmd_events,
        'training': self.cmd_training,

        # Enhanced Bell System commands
        '3a': self.cmd_3a,
        '5ess': self.cmd_5ess,
        'bsp': self.cmd_bsp,
        'western': self.cmd_western,
        'coer': self.cmd_coer,
        'lmos': self.cmd_lmos,
        'tnds': self.cmd_tnds,
        'sarts': self.cmd_sarts,
        'radio': self.cmd_radio,
        'microwave': self.cmd_microwave,
        'satellite': self.cmd_satellite,
        'alarm': self.cmd_alarm,
        'nroff': self.cmd_nroff,
        'troff': self.cmd_troff,
        'tbl': self.cmd_tbl,
        'eqn': self.cmd_eqn,
        'pic': self.cmd_pic,
        'refer': self.cmd_refer,
        'send': self.cmd_send,
        'rjestat': self.cmd_rjestat,
        't1carrier': self.cmd_t1carrier,
        'lcarrier': self.cmd_lcarrier,
        'multiplex': self.cmd_multiplex,
        'regenerator': self.cmd_regenerator,
        'antenna': self.cmd_antenna,

        # Enhanced UX commands
        'errors': self.cmd_errors,
        'verbosity': self.cmd_verbosity,
        'history': self.cmd_history,
        'set': self.cmd_set,
        'clli': self.cmd_clli,
        'cosmos': self.cmd_cosmos,

        # Repair service bureau, loop testing and the craft record
        'report': self.cmd_report,
        'mlt': self.cmd_mlt,
        'testline': self.cmd_testline,
        'qual': self.cmd_qual,
        'hint': self.cmd_hint,
        'write': self.cmd_write,
        'mail': self.cmd_mail,
        'orderwire': self.cmd_orderwire,
        'testcall': self.cmd_testcall,

        # The shell: moving around, reading, text handling
        'cd': self.cmd_cd,
        'cp': self.cmd_cp,
        'mv': self.cmd_mv,
        'rm': self.cmd_rm,
        'mkdir': self.cmd_mkdir,
        'rmdir': self.cmd_rmdir,
        'touch': self.cmd_touch,
        'chmod': self.cmd_chmod,
        'du': self.cmd_du,
        'find': self.cmd_find,
        'tty': self.cmd_tty,
        'sync': self.cmd_sync,
        'tr': self.cmd_tr,
        'cut': self.cmd_cut,
        'sed': self.cmd_sed,
        'tee': self.cmd_tee,
        'rev': self.cmd_rev,
        'cmp': self.cmd_cmp,
        'diff': self.cmd_diff,
        'od': self.cmd_od,
        'spell': self.cmd_spell,
        # The rest of the Seventh Edition text tools.
        'pr': self.cmd_pr,
        'comm': self.cmd_comm,
        'join': self.cmd_join,
        'look': self.cmd_look,
        'split': self.cmd_split,
        'sum': self.cmd_sum,
        'dd': self.cmd_dd,
        'expr': self.cmd_expr,
        'basename': self.cmd_basename,
        'true': self.cmd_true,
        'false': self.cmd_false,
        # Deferred work, builds and the uucp network.
        'at': self.cmd_at,
        'make': self.cmd_make,
        'su': self.cmd_su,
        'logname': self.cmd_logname,
        'uuname': self.cmd_uuname,
        'uulog': self.cmd_uulog,
        'uux': self.cmd_uux,
        'kill': self.cmd_kill,
        'nice': self.cmd_nice,
        'time': self.cmd_time,
        'nohup': self.cmd_nohup,
        'banner': self.cmd_banner,
        'factor': self.cmd_factor,
        'primes': self.cmd_primes,
        'bc': self.cmd_bc,
        'units': self.cmd_units,
        'sleep': self.cmd_sleep,
        'mesg': self.cmd_mesg,
        'wall': self.cmd_wall,
        'passwd': self.cmd_passwd,
        'stty': self.cmd_stty,
        'fortune': self.cmd_fortune,
        'bcd': self.cmd_bcd,
        'ppt': self.cmd_ppt,
        'arithmetic': self.cmd_arithmetic,
        'moo': self.cmd_moo,
        'readnews': self.cmd_readnews,
        'ed': self.cmd_ed,
        'cc': self.cmd_cc,
        'cat': self.cmd_cat,
        'more': self.cmd_more,
        'head': self.cmd_head,
        'tail': self.cmd_tail,
        'grep': self.cmd_grep,
        'wc': self.cmd_wc,
        'sort': self.cmd_sort,
        'uniq': self.cmd_uniq,
        'echo': self.cmd_echo,
        'file': self.cmd_file,
        'cal': self.cmd_cal,

        # Standard UNIX commands
        'ps': self.cmd_ps,
        'who': self.cmd_who,
        'ls': self.cmd_ls,
        'pwd': self.cmd_pwd,
        'date': self.cmd_date,
        'df': self.cmd_df,
        'help': self.cmd_help,
        'man': self.cmd_man,
        'status': self.cmd_status,
        'test': self.cmd_test,
        'quit': self.cmd_quit,
        'clear': self.cmd_clear
        }
