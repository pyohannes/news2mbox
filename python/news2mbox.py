#### +                                  
#### vim: ai softtabstop=2 shiftwidth=2
#```((mode docu) (post ("replace-variables")))
# \documentclass[11pt,a4paper]{article}
#   
# \usepackage{listings}
# \usepackage{tabularx}
# \usepackage{fullpage}
#
# \lstset{
#   basicstyle=\ttfamily,
#   xleftmargin=15pt,
#   basewidth={.48em}
# }
#
# \newcommand{\tc}{\texttt}
# \newcommand{\ti}{\textit}
#
# \setlength{\parindent}{0pt}
#
# \title{``(file-basename)``}
#
# \begin{document}
#  \maketitle
#  \section{Introduction}
#
#   \ti{news2mbox} is a program that fetches newsgroup messages from NNTP
#   servers and writes the messages to mailboxes of the \ti{mbox} format for
#   offline reading with MUAs like \ti{mutt}.
#
#   Messages are fetched cumulatively, with each subsequent call of
#   \ti{news2mbox} only new messages are fetched.
#
#  \section{Dependencies}
#```
##!/usr/bin/env python3
#```
#   \ti{news2mbox} is written to work on Python 3. No attempts are made to
#   provide compabitility with Python 2.
#```
import argparse
#```
#   Command line arguments are processed via the \tc{argparse} Python module.
#```
import nntplib
#```
#   \tc{nntplib} is at the core of \ti{news2mbox}. This module of the standard
#   Python library is used to connect to NNTP servers, to fetch messages and
#   message meta information.
#```
import json
#```
#   All configuration and status files \ti{news2mbox} uses are stored in the
#   JSON format. On the implementation side, Python data structures can be
#   converted to and from JSON in a very simple and concise way. On the user
#   side the user need not struggle with another configuration file format, as
#   JSON is very prominent and widely known.
#
#   Besides that, only two other modules are used:
#```
import os
import sys
import time
#```
#   The \tc{os} and \tc{sys} module are needed for obvious reasons, the 
#   \tc{time} module to format time stamps used in converting messages to the 
#   \ti{mbox} format.\newline
#
#
# \section{Configuration and status files}
#
# \subsection{\tc{config.json}}
#
#  The main configuration file \tc{config.json} contains a list of all news
#  servers with login data and a list of groups for which messages should be
#  obtained.
#
#   \begin{table}[h]
#  \center
#  {\it
#  \begin{tabular}{llll}
#   \{ & ``server'' & : & ``news.server.com'', \\
#    & ``user''   & : & ``username'', \\
#    & ``password''   & : & ``secret'', \\
#    & ``groups''   & : & [ ``comp.lang.python'', ``comp.lang.c'' ] \} \\
#  \end{tabular}
#  }
#  \caption{A sample configuration file}
#   \end{table}
#
#  The function \tc{read\_config} parses those configuration files:
#```
def read_config(cfg):
  keywords = [ 'server', 'user', 'password', 'groups', 'outdir', 'ssl' ]
#```
#  The configuration for every server is stored in an object that can have the
#  following keys and values:\newline
#
#  \begin{tabularx}{\linewidth}{lX}
#   Key & Value \\ \hline 
#   server & The address of the NNTP server as string. This value is required. \\
#   user & The user name for the NNTP login as string. \\
#   password & The password for the NNTP login as string. \\
#   groups & A list of strings of newsgroup names. This value is required. \\
#   outdir & A directory in which the mbox files are written. If this value is
#   not given, the directory defaults to \tc{\$HOME/news}. \\
#   ssl & \ti{false} if no SSL connection to the NNTP server should be used.
#   The default is \ti{true}. \\
#  \end{tabularx}\newline
#
#  First the file is parsed into a JSON data structure:
#```
  with open(cfg, 'r') as f:
    try:
      servers = json.load(f)
    except Exception as e:
      raise SyntaxError(str(e))
#```
#  The configuration file can either contain only one JSON object representing 
#  a server configuration or it can contain a list of such objects. This avoid
#  superfluous braces in the configuration file. In the first case the single
#  object is put into an one-element list:
#```
  if not isinstance(servers, list):
    servers = [ servers ]
#```
#  Then follows some cumbersome code ensuring the validity of the
#  configuration object.
#```
  for s in servers:
#```
#  configuration object. The following requirements must be fullfilled by a
#  valid configuration object:
#
#  \begin{enumerate}
#   \item It must define a server.
#```
    if not 'server' in s:
      raise SyntaxError('"server" missing in configuration %s' % s)
#```
#   \item It must define groups.
#```
    if not 'groups' in s:
      raise SyntaxError('"groups" missing in configuration %s' % s)
#```
#   \item The value for \ti{groups} must be a list of strings.
#```
    for key, value in s.items():
      if key == 'groups':
        if not isinstance(value, list):
          raise SyntaxError(
            '"groups" must be a list, but is %s' % value)

      elif key == 'ssl':
        if not isinstance(value, bool):
          raise SyntaxError(
            '"ssl" must be a bool, but is %s' % value)
#```
#   \item All other values must be strings.
#```
      elif key in keywords:
        if not isinstance(value, str):
          raise SyntaxError(
            '"%s" must be a str, but is %s' % (key, value))
#```
#   \item The object must not contain unknown keywords.
#```
      else:
        raise SyntaxError('Unknown key "%s" in %s' % (key, cfg))
#```
#  \end{enumerate}
#
#  Finally the list of valid server configurations is returned:
#```
  return servers

#```
#  \section{Status file - \tc{status.json}}
#```
def read_status(statusfile):
  status = {}

  if os.path.exists(statusfile):
    try:
      with open(statusfile, 'r') as f:
        status = json.load(f)

      if not isinstance(status, dict):
        raise SyntaxError(
          'Error reading "%s": root must be a dict' % statusfile)
      for k, v in status.items():
        if not isinstance(k, str):
          raise SyntaxError(
            'Error reading "%s": invalid format of key %s' % (
              statusfile, k))
        if not isinstance(v, int):
          raise SyntaxError(
            'Error reading "%s": invalid format of value %s' % (
              statusfile, v))
    except: pass

  return status


def write_status(statusfile, status):
  with open(statusfile, 'w') as f:
    json.dump(status, f)


#```
#  \section{Conversion to the mbox format}
#```
def make_mbox_header(message_id):
  return 'From %s %s' % (
    message_id.strip('<>'), 
    time.strftime('%a %b %e %H:%M:%S %Z %Y'))


#```
#  \section{Reading messages from the server}
#```
def read_messages(config, status):
  print('Connecting to %s ... ' % config['server'], end='')
  s = nntplib.NNTP(config['server'])
  if config['ssl']:
    s.starttls()
  s.login(user=config.get('user'), password=config.get('password'))
  print('done.')

  try:
    for g in config['groups']:
      resp, count, first, last, name = s.group(g)
      last = int(last)
      first = max(status.get(g, 0), last-200)
      no_messages = last - first

      lines = []
      for relnum, absnum in enumerate(range(first + 1, last + 1)):
        print('Getting message %d of %d for %s' % (relnum, no_messages, g), end='')
        resp, info = s.article(absnum)
        lines.append(make_mbox_header(info.message_id))
        lines.extend([ m.decode('utf-8', errors='ignore') for m in info.lines])
        print('.')
    
      with open(os.path.join(config['outdir'], g), 'a') as f:
        for line in lines:
          f.write(line)
          f.write('\n')

      status[g] = last
  finally:
    s.quit()

#```
#  \section{Program invocation and usage}
#
#  \subsection{Command line arguments}
#```
PROGRAM = 'news2mbox'
VERSION = '0.1'

def parse_arguments():
  parser = argparse.ArgumentParser(prog=PROGRAM)

  parser.add_argument('-c', '--config-dir',
    dest='configdir',
    default=os.path.join(os.environ['HOME'], '.%s' % PROGRAM),
    help='Directory where configuration and status files are stored')
  parser.add_argument('--version',
    action='store_true',
    dest='version',
    default=False,
    help='Display version information')
  
  return parser.parse_args()

#```
#  \subsection{Main program loop}
#```
if __name__ == '__main__':      
                                     
  args = parse_arguments()

  if args.version:
    print('This is %s version %s' % (PROGRAM, VERSION))
    sys.exit(0)

  statusfile = os.path.join(args.configdir, 'status.json')
  configfile = os.path.join(args.configdir, 'config.json')

  status = read_status(statusfile)
  configs = read_config(configfile)

  try:
    for config in configs:

      config['outdir'] = os.path.expandvars(
              config.get('outdir', '$HOME/news'))
      if not 'ssl' in config:
        config['ssl'] = True

      read_messages(config, status)
  finally:
    write_status(statusfile, status)
#```
# \end{document}
