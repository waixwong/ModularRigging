__author__ = 'WEI'
from __future__ import print_function

import re
import sys
import time
import os.path
import textwrap

from telnetlib import Telnet

# Our default plugin settings
_settings = {
    'host': '127.0.0.1',
    'mel_port': 7001,
    'py_port': 7002
}


class send_to_mayaCommand():
    # A template wrapper for sending Python source safely
    # over the socket.
    # Executes in a private namespace to avoid collisions
    # with the main environment in Maya.
    # Also handles catches and printing exceptions so that
    # they are not masked.
    PY_CMD_TEMPLATE = textwrap.dedent('''
		import traceback
		import __main__

		namespace = __main__.__dict__.get('_sublime_SendToMaya_plugin')
		if not namespace:
			namespace = __main__.__dict__.copy()
			__main__.__dict__['_sublime_SendToMaya_plugin'] = namespace

		namespace['__file__'] = {2!r}

		try:
			{0}({1!r}, namespace, namespace)
		except:
			traceback.print_exc()
	''')

    # Match single-line comments in MEL/Python
    RX_COMMENT = re.compile(r'^\s*(//|#)')

    def run(self, edit):

        # Do we have a valid source language?
        syntax = self.view.settings().get('syntax')

        if re.search(r'python', syntax, re.I):
            lang = 'python'
            sep = '\n'

        elif re.search(r'mel', syntax, re.I):
            lang = 'mel'
            sep = '\r'

        else:
            print('No Maya-Recognized Language Found')
            return

        isPython = (lang == 'python')

        host = _settings['host']
        port = _settings['py_port'] if lang == 'python' else _settings['mel_port']

        # Check the current selection size to determine
        # how we will send the source to be executed.
        selections = self.view.sel()  # Returns type sublime.RegionSet
        selSize = 0
        for sel in selections:
            if not sel.empty():
                selSize += 1

        snips = []

        # If nothing is selected, we will use an approach that sends an
        # entire source file, and tell Maya to execute it.
        if selSize == 0:

            execType = 'execfile'
            print("Nothing Selected, Attempting to exec entire file")

            if self.view.is_dirty():
                sublime.error_message("Save Changes Before Maya Source/Import")
                return

            file_path = self.view.file_name()
            if file_path is None:
                sublime.error_message("File must be saved before sending to Maya")
                return

            plat = sublime_plugin.sys.platform
            if plat == 'win32':
                file_path = file_path.replace('\\', '\\\\')
                print("FILE PATH:", file_path)

            if lang == 'python':
                snips.append(file_path)
            else:
                snips.append('rehash; source "{0}";'.format(file_path))

        # Otherwise, we are sending snippets of code to be executed
        else:
            execType = 'exec'
            file_path = ''

            substr = self.view.substr
            match = self.RX_COMMENT.match

            # Build up all of the selected lines, while removing single-line comments
            # to simplify the amount of data being sent.
            for sel in selections:
                snips.extend(line for line in substr(sel).splitlines() if not match(line))

        mCmd = str(sep.join(snips))
        if not mCmd:
            return

        print('Sending {0}:\n{1!r}\n...'.format(lang, mCmd[:200]))

        if lang == 'python':
            # We need to wrap our source string into a template
            # so that it gets executed properly on the Maya side
            mCmd = self.PY_CMD_TEMPLATE.format(execType, mCmd, file_path)

        c = None

        try:
            c = Telnet(host, int(port), timeout=3)
            c.write(mCmd)

        except Exception:
            e = sys.exc_info()[1]
            err = str(e)
            sublime.error_message(
                "Failed to communicate with Maya (%(host)s:%(port)s)):\n%(err)s" % locals()
            )
            raise

        else:
            time.sleep(.1)

        finally:
            if c is not None:
                c.close()