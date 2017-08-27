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
#   \ti{news2mbox} is a program that fetches newsgroup articles from NNTP
#   servers and writes those articles to mailboxes of the \ti{mbox} format for
#   offline reading with MUAs like \ti{mutt}.
#
#   Articles are fetched cumulatively, with each subsequent call of
#   \ti{news2mbox} only new articles are fetched.
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
#   Python library is used to connect to NNTP servers, to fetch articles and
#   article meta information.
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
#   \tc{time} module to format time stamps used in converting articles to the 
#   \ti{mbox} format.\newline
#
#
# \section{Configuration and status files}
#
# \subsection{\tc{config.json}}
# \label{sec:readconfigs}
#
#  The main configuration file \tc{config.json} contains a list of all news
#  servers with login data and a list of groups for which articles should be
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
#   \item The value for \ti{groups} must be a list of strings. The value of
#   \ti{ssl} must be a boolean.
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
#  \label{sec:readstatus}
#
#  The status file \tc{status.json} holds a dictionary that contains the number
#  of the last obtained article for all configured news groups. This file is
#  not supposed to be edited by the user.

#  \begin{table}[h]
#   \center
#   {\it
#   \begin{tabular}{llll}
#    \{ & ``comp.lang.c'' & : & 12496, \\
#     & ``comp.lang.scheme''   & : & 188, \\
#     & ``comp.lang.python''   & : & 8638 \} \\
#   \end{tabular}
#   }
#   \caption{A sample status file}
#  \end{table}
#
#  The function \tc{read\_status} reads a status file, verifies the content and
#  returns the data as a dictionary holding newsgroup names as keys and integer 
#  article numbers as data.
#```
def read_status(statusfile):
#```
#  The file is opened and its JSON content is parsed.
#```
  try:
    with open(statusfile, 'r') as f:
      status = json.load(f)
#```
#  Then the structure of the data is verified: the root object must be a
#  dictionary, all its keys must be strings and all its values must be 
#  integers.
#```
    if not isinstance(status, dict):
      raise SyntaxError()
    for k, v in status.items():
      if not isinstance(k, str):
        raise SyntaxError()
      if not isinstance(v, int):
        raise SyntaxError()
#```
#  In case the file does not exists, cannot be read or parsed or its data
#  cannot be verified an empty dictionary is returned.
#```
  except:
    status = {}

  return status

#```
#  Writing the status file is very straight forward. As the status data is
#  handled internally its integrity can be assumed. So the status data simply
#  needs to be dumped as serialized JSON data into the file:
#```
def write_status(statusfile, status):
  with open(statusfile, 'w') as f:
    json.dump(status, f)
#```
#  \section{Conversion to the mbox format}
#
#  Newsgroups articles can be stored \ti{mbox} mailboxes as is, they just need
#  to be prepended with a proper \ti{mbox} header line. This header line
#  consists of the string \ti{``From''}, followed by the message id and a time
#  stamp. The function \tc{make\_mbox\_header} constructs and returns this
#  header line. The string is encoded, as subsequently all \ti{mbox} files and
#  newsgroup articles are never decoded and treated as binary data.
#```
def make_mbox_header(message_id):
  return ('From %s %s' % (
    message_id.strip('<>'), 
    time.strftime('%a %b %e %H:%M:%S %Z %Y'))).encode()
#```
#  \section{Reading articles from the server}
#  \label{sec:readarticles}
#
#  The core task of \ti{news2mbox} is reading messges from the NNTP servers and
#  writing those message into local mailboxes. These functionality is
#  encapsulated in the function \tc{read\_articles}. The function gets the
#  argument \tc{config} which is a dictionary obtained from the configuration 
#  file \tc{config.json} and holds information about a server with connection
#  information and a list of news groups. The \tc{status} argument is a
#  dictionary obtained from the file \tc{status.json} holding information to
#  identify the last article read for each news group.
#```
def read_articles(config, status):
#```
#  The algorithm works in five steps:
#  \begin{enumerate}
#  \item \ti{The connection to the NNTP is established.} The server address,
#  username and password are taken from the \tc{config} dictionary. Username
#  and password are optional and can therefore be \tc{None}. Depending on the 
#  configuration an SSL connection is established.
#```
  with nntplib.NNTP(config['server']) as s:
    if config['ssl']:
      s.starttls()
    s.login(user=config.get('user'), password=config.get('password'))

#```
#  The following steps are done for each news group configured.
#```
    for g in config['groups']:
#```
#  \item \ti{The range of article numbers to be read is determined.} For this 
#  purpose, the last available article number is obtained from the server.
#```
      resp, count, first, last, name = s.group(g)
      last = int(last)
#```
#  The number of the first article to be read is set to the number of the last 
#  article for this news group. This information is obtained from the status
#  dictionary. The number is set to 0 if no status information is available for
#  this group. As a hard coded limit, at most 200 articles can be read, so the 
#  upper limit for the number of the first article is \ti{last - 200}. One is
#  added to obtain the number of the first unread articles. This turns the
#  default 0 into 1, as by the standard article numbers start with 1.
#```
      first = max(status.get(g, 0), last-200) + 1
#```
#   Calculating the number of all articles that will be read is trivial. This
#   number is used to print status information.
#```
      no_articles = last - first + 1
#```
#  The status information printed is modeled after the output of the famous
#  \ti{fetchmail} utility.
#```
      if no_articles:
        print('%d articles for %s at %s.' % 
          (no_articles, g, config['server']))
      else:
        print('%s: No new articles for %s at %s' % 
          (PROGRAM, g, config['server']))

#```
#  \item \ti{Articles are read from the server.} The articles are stored line
#  wise in a list of lines.
#```
      lines = []
#```
#  The main loop reading articles loops over two values: \tc{relnum} denotes
#  the relative number of the article, starting with 1, \tc{absnum} denots the
#  article number as known to the server, from \tc{first} to \tc{last}.
#```
      for relnum, absnum in enumerate(range(first, last + 1), 1):
#```
#  It is then tried to read a article from the server. If this fails, the
#  status information line is ended with the string \ti{not found} and the next
#  article number is processed.
#```
        print('reading article %s: %d of %d ' % 
          (g, relnum, no_articles), end='')
        try:
            resp, info = s.article(absnum)
        except nntplib.NNTPError:
            print('not found.')
            continue
#```
#  If a article is read, first a header for this article is appended to the
#  list of lines. Then the lines of the article are stored as is and the status
#  line is ended with the string \ti{flushed}.
#
#  Here it is to be noted that all article lines obtained via the NNTP server
#  are handled as byte sequences and are never decoded.
#```
        lines.append(make_mbox_header(info.message_id))
        lines.extend(info.lines)
        print('flushed')
#```
#  \item \ti{The mailbox file is written.} Then all the lines are appended to 
#  the mailbox file in the destined output directory. For performance reasons, 
#  this is done in a verbose \tc{for} loop to avoid all string concantenation.
#```
      with open(os.path.join(config['outdir'], g), 'ab') as f:
        for line in lines:
          f.write(line)
          f.write('\n'.encode())

#```
#  \item \ti{The status information is updated.} The entry for this newsgroup in 
#  the status dictionary set to the number of the last article that was read
#  for this group.
#```
      status[g] = last
#```
#  \end{enumerate}
#
#  \section{Program invocation and usage}
#
#  \subsection{Command line arguments}
#  \label{sec:argparser}
#
#  The program name and the program version are set here.
#```
PROGRAM = 'news2mbox'
VERSION = '0.1'
#```
#  The function \tc{parse\_arguments} creates an argument parser and parses
#  command line arguments. Currently
#  three arguments are supported: \tc{-c} for specifing a configuration
#  directory, \tc{--version} for printing version information and the
#  \tc{--help} provided by the \tc{argparse} module.\newline
#
#  Here it is to be noted that the configuration directory is set to the
#  default value \tc{\$HOME/.news2box} if none is given by the user.
#```
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
#```
#  The main program involves four steps:
#
#  \begin{enumerate}
#   \item \ti{Arguments are parsed.} The parsing is done by the function
#   \tc{parse\_arguments} described in section \ref{sec:argparser}. If the
#   version argument is given, the version information is printed and then the
#   program exits.
#```
  args = parse_arguments()

  if args.version:
    print('This is %s version %s' % (PROGRAM, VERSION))
    sys.exit(0)
#```
#  \item \ti{Status and configuration files are read.} In this step paths to
#  the status and configuration file are created. The files are located in the
#  configuration directory, the status file is called \tc{status.json} and  
#  the configuration file is called \tc{config.json}. \newline
#
#  The files are then read via the functions \tc{read\_status} which is
#  described in section \ref{sec:readstatus} and \tc{read\_configs} which is
#  described in section \ref{sec:readconfigs}. 
#```
  statusfile = os.path.join(args.configdir, 'status.json')
  configfile = os.path.join(args.configdir, 'config.json')
  status = read_status(statusfile)
  configs = read_config(configfile)
#```
#  \item \ti{Read articles for each server.} Then follows the loop over the
#  list of server configurations.
#```
  try:
    for config in configs:
#```
#  Here some default configuration values are set. If not output directory is
#  specified in the configuration, it is set to \tc{\$HOME/news}. Environment
#  variables used in this configuration property are replaced by their values.
#```
      config['outdir'] = os.path.expandvars(
              config.get('outdir', '$HOME/news'))
#```
#  SSL usage is turned on if no other information is specified in the
#  configuration.
#```
      if not 'ssl' in config:
        config['ssl'] = True
#```
#  Finally the articles for the configuration are read via the function
#  \tc{read\_articles} described in section \ref{sec:readarticles}.
#```
      read_articles(config, status)
#```
#  \item \ti{Write status information.} The function \tc{read\_message} updates
#  the information in the \tc{status} dictionary. This information is written
#  back into the status file for the use by future invocations of 
#  \ti{news2mbox}. This is done via the function \tc{write\_status} describes
#  in section \ref{sec:readstatus}.
#```
  finally:
    write_status(statusfile, status)
#```
#  \end{enumerate}
#
# \section{References}
#
#  \tc{https://docs.python.org/3/} offers high quality documentation for all
#  Python modules used.\newline
#
#  At \tc{https://tools.ietf.org/html/rfc3977} a full specification of the NNTP
#  protocol can be found.

# \end{document}
