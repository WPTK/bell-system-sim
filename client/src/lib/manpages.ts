// Collection of manual pages for UNIX commands

const manPages: Record<string, string> = {
  ls: `
LS(1)                     UNIX Programmer's Manual                      LS(1)

NAME
     ls - list contents of directory

SYNOPSIS
     ls [ -acdfgilqrstu ] name ...

DESCRIPTION
     For each directory argument, ls lists the contents of the directory; for
     each file argument, ls repeats its name and any other information
     requested. The output is sorted alphabetically by default. When no argu-
     ment is given, the current directory is listed. When several arguments
     are given, the arguments are first sorted appropriately, but file argu-
     ments appear before directories and their contents.

OPTIONS
     -a  List all entries; usually entries that begin with . are not listed.
     -c  Use time of last modification to inode for sorting or printing.
     -d  If argument is a directory, list only its name, not its contents.
     -f  Force each argument to be interpreted as a directory and list it.
     -g  List in long format, same as -l but omit the owner.
     -i  Print i-number in first column of the report for each file.
     -l  List in long format, giving mode, owner, size in bytes, time.
     -q  Force printing of non-graphic characters in file names as ?.
     -r  Reverse the order of sort to get reverse alphabetic or oldest first.
     -s  Give size in 512-byte blocks, including indirect blocks.
     -t  Sort by time modified instead of by name.
     -u  Use time of last access for sorting or printing.
  `,
  
  cd: `
CD(1)                     UNIX Programmer's Manual                      CD(1)

NAME
     cd - change working directory

SYNOPSIS
     cd [ directory ]

DESCRIPTION
     Directory becomes the new working directory. The process must have exe-
     cute (search) permission in directory. If no directory is specified, the
     home directory is used.

     The cd command is built into the shell.
  `,
  
  pwd: `
PWD(1)                    UNIX Programmer's Manual                     PWD(1)

NAME
     pwd - working directory name

SYNOPSIS
     pwd

DESCRIPTION
     Pwd prints the pathname of the working (current) directory.
  `,
  
  cat: `
CAT(1)                    UNIX Programmer's Manual                     CAT(1)

NAME
     cat - concatenate and print

SYNOPSIS
     cat [ -u ] [ file ... ]

DESCRIPTION
     Cat reads each file in sequence and writes it on the standard output. If
     no input file is given, or if the argument '-' is encountered, cat reads
     from the standard input. The -u option causes the output to be unbuf-
     fered.

     The cat utility is useful for displaying files to the screen, and for
     concatenating several files together.
  `,
  
  echo: `
ECHO(1)                   UNIX Programmer's Manual                    ECHO(1)

NAME
     echo - echo arguments

SYNOPSIS
     echo [ arg ... ]

DESCRIPTION
     Echo writes its arguments separated by blanks and terminated by a new-
     line on the standard output. It also understands C-like escape conven-
     tions; beware of conflicts with the shell's use of \\:

     \\b   backspace
     \\c   print line without newline
     \\f   form-feed
     \\n   newline
     \\r   carriage return
     \\t   tab
     \\v   vertical tab
     \\\\   backslash
     \\0n  where n is 1 to 3 octal digits, the ASCII character with that value

     Echo is useful for producing diagnostics in command files and for send-
     ing known data into a pipe.
  `,
  
  mkdir: `
MKDIR(1)                  UNIX Programmer's Manual                   MKDIR(1)

NAME
     mkdir - make a directory

SYNOPSIS
     mkdir [ -p ] dirname ...

DESCRIPTION
     Mkdir creates specified directories in mode 777 (possibly altered by the
     user's umask, see umask(2)). Standard entries '.' and '..' are made
     automatically.

     The -p option allows parent directories that do not exist to be created
     as needed.

     Mkdir requires write permission in the parent directory.
  `,
  
  rm: `
RM(1)                     UNIX Programmer's Manual                      RM(1)

NAME
     rm - remove (unlink) files

SYNOPSIS
     rm [ -fri ] file ...

DESCRIPTION
     Rm removes the entries for one or more files from a directory. If an
     entry was the last link to the file, the file is destroyed. Removal of a
     file requires write permission in its directory, but neither read nor
     write permission on the file itself.

     If a file has no write permission and the standard input is a terminal,
     its permissions are printed and a line is read from the standard input.
     If that line begins with 'y' the file is deleted, otherwise the file
     remains.

     Options:
     -f    Force files to be removed without displaying permissions, asking
           questions or reporting errors.
     -r    Recursively delete the contents of directories, including any
           subdirectories.
     -i    Ask whether to delete each file, and, if -r is also specified,
           whether to examine each directory.
  `,
  
  cp: `
CP(1)                     UNIX Programmer's Manual                      CP(1)

NAME
     cp - copy

SYNOPSIS
     cp [ -i ] [ -r ] file1 file2
     cp [ -i ] [ -r ] file ... directory

DESCRIPTION
     In the first form, the cp utility copies the contents of file1 to file2.
     In the second form, cp copies each file to the specified directory. The
     mode and owner of file2 are preserved if it already existed; the mode of
     the source file is used otherwise.

     If cp detects an attempt to copy a file to itself, the copy will fail.

     Cp refuses to copy a file onto a link to itself.

     Options:
     -i    Interactive mode. Prompt for confirmation whenever the copy would
           overwrite an existing file. A y in answer confirms the copy.
     -r    If file1 is a directory, cp copies the directory and all its files,
           including any subdirectories and their files to file2. Either name
           can be a directory.
  `,
  
  mv: `
MV(1)                     UNIX Programmer's Manual                      MV(1)

NAME
     mv - move or rename files

SYNOPSIS
     mv [ -f ] [ -i ] file1 file2
     mv [ -f ] [ -i ] file ... directory

DESCRIPTION
     Mv moves (changes the name of) file1 to file2.

     If file2 already exists, it is removed before file1 is moved. If file2
     has a mode which forbids writing, mv prints the mode and reads the stan-
     dard input to obtain a line; if the line begins with y, the move takes
     place, if not, mv exits.

     In the second form, one or more files are moved to the directory with
     their original file-names.

     Mv refuses to move a file onto itself.

     Options:
     -f    Force the move without displaying permissions and asking questions.
     -i    Interactive mode. Prompt for confirmation whenever the move would
           overwrite an existing file. A y in answer confirms the move.
  `,
  
  chmod: `
CHMOD(1)                  UNIX Programmer's Manual                   CHMOD(1)

NAME
     chmod - change mode

SYNOPSIS
     chmod [ -R ] mode file ...

DESCRIPTION
     The mode of each named file is changed according to mode, which may be
     absolute or symbolic.  An absolute mode is an octal number constructed
     from the OR of the following modes:

     4000    set user ID on execution
     2000    set group ID on execution
     1000    sticky bit
     0400    read by owner
     0200    write by owner
     0100    execute (search in directory) by owner
     0070    read, write, execute (search) by group
     0007    read, write, execute (search) by others

     A symbolic mode has the form:
     [ who ] op permission [ op permission ] ...

     The who part is a combination of the letters u (for user's permissions),
     g (group) and o (other). The letter a stands for ugo, the default if who
     is omitted.

     Op can be + to add permission to the file's mode, - to take away permis-
     sion, or = to assign permission absolutely (all other bits will be
     reset).

     Permission is any combination of the letters r (read), w (write), x (exe-
     cute), s (set owner or group id) and t (save text - sticky).

     Options:
     -R    Recursively descend through directory arguments, changing the mode
           of all files in the directory.
  `,
  
  chown: `
CHOWN(1)                  UNIX Programmer's Manual                   CHOWN(1)

NAME
     chown - change owner

SYNOPSIS
     chown [ -R ] owner[.group] file ...

DESCRIPTION
     Chown changes the owner of the files to owner, which may be either a
     decimal UID or a login name found in the password file. The owner may be
     followed by a period and a group name (or number), in which case the
     group ID of the files is changed as well.

     Only the super-user can change owner, in order to simplify accounting
     procedures.

     Options:
     -R    Recursively descend through directory arguments, setting the
           specified owner (and group) ID.

     Files are not followed if they are symbolic links.
  `,
  
  grep: `
GREP(1)                   UNIX Programmer's Manual                    GREP(1)

NAME
     grep - search a file for a pattern

SYNOPSIS
     grep [ -bcilnsvw ] [ -e ] expression [ file ... ]

DESCRIPTION
     Grep searches the input files (standard input default) for lines match-
     ing the regular expression. Normally, each line found is copied to the
     standard output. If the -v flag is used, all lines but those matching are
     printed. If no files are specified, grep assumes standard input.

     Options:
     -b    Tab characters in the matched line are replaced by spaces, with
           stops set at every 8 positions.
     -c    Only a count of matching lines is printed.
     -i    The case of letters is ignored in making comparisons.
     -l    The names of files with matching lines are listed (once) separated
           by newlines.
     -n    Each output line is preceded by its relative line number in the
           file, starting at 1.
     -s    Silent mode. Nothing is printed except error messages.
     -v    All lines but those matching are printed.
     -w    The expression is searched for as a word (as if surrounded by
           '\\<' and '\\>').
     -e    Same as a simple expression argument, but useful when the expres-
           sion begins with a '-'.

     In all cases the file name is shown if there is more than one input file.
     Care should be taken when using the characters $ * [ ^ | ( ) and \\ in the
     expression as they are also meaningful to the Shell. It is safest to
     enclose the entire expression argument in single quotes ' '.
  `,
  
  wc: `
WC(1)                     UNIX Programmer's Manual                      WC(1)

NAME
     wc - word count

SYNOPSIS
     wc [ -lwc ] [ file ... ]

DESCRIPTION
     Wc counts lines, words and characters in the named files, or in the stan-
     dard input if no files appear. A word is a maximal string of characters
     delimited by spaces, tabs or newlines.

     If an argument is present, it may contain the following options:
     -l    Count lines.
     -w    Count words.
     -c    Count characters.

     The default is -lwc.
  `,
  
  man: `
MAN(1)                    UNIX Programmer's Manual                     MAN(1)

NAME
     man - find manual information by keywords; print out the manual

SYNOPSIS
     man [ - ] [ -k ] keyword ...
     man [ - ] [ -n ] [section] title ...

DESCRIPTION
     Man is a program which gives information from the programmers manual. It
     can be asked for one line descriptions of commands specified by name, or
     for all commands whose description contains any of a set of keywords. It
     can also provide on-line access to the sections of the printed manual.

     When given the option -k and a set of keywords, man prints out a one line
     synopsis of each command in the manual whose description contains one of
     those keywords.

     When given a title, man provides on-line access to the manual section for
     that title. The section can be specified with the optional section argu-
     ment, which can be either a number (1 through 8), or one of the words
     'local', 'new', or 'old'.

     The - flag causes man to print out the manual section on the standard
     output, rather than invoking more(1) to print it. This is useful when
     the output is to be a file or a pipe.

     If the optional section argument is omitted, man searches in the order
     specified by the MANPATH environment variable, or by a default list of
     directories.
  `,
  
  who: `
WHO(1)                    UNIX Programmer's Manual                     WHO(1)

NAME
     who - who is on the system

SYNOPSIS
     who [ who-file ] [ am i ]

DESCRIPTION
     Who, without an argument, lists the login name, terminal name, and login
     time for each current system user.

     If a file is given, the information is taken from that file instead of
     /etc/utmp. Typically the file is /etc/wtmp, which contains a history of
     all the logins since the file was last created.

     Who am i (or who am I) tells who you are logged in as.
  `,
  
  date: `
DATE(1)                   UNIX Programmer's Manual                    DATE(1)

NAME
     date - print and set the date

SYNOPSIS
     date [ -u ] [ yymmddhhmm[.ss] ] [ +format ]

DESCRIPTION
     If no argument is given, the current date and time are printed. Providing
     an argument sets the date; only the super-user can set the date.

     Yy, mm, dd, hh and mm are the last two digits of the year, month (01-12),
     day (01-31), hour (00-23), and minute (00-59), respectively. The optional
     ss is the seconds (00-59).

     If the argument begins with +, the output of date is under control of the
     user. The format for the output is similar to that of printf. Each % is
     replaced by a substitution from the following list:
     %n    insert a newline character
     %t    insert a tab character
     %m    month of year (01-12)
     %d    day of month (01-31)
     %y    last 2 digits of year (00-99)
     %D    date as %m/%d/%y
     %H    hour (00-23)
     %M    minute (00-59)
     %S    second (00-59)
     %T    time as %H:%M:%S
     %j    day of the year (001-366)
     %w    day of week (0-6) with 0=Sunday
     %a    abbreviated weekday (Sun-Sat)
     %h    abbreviated month (Jan-Dec)
     %r    time in AM/PM notation

     Options:
     -u    Display (or set) the date in GMT (universal) time.
  `,
  
  touch: `
TOUCH(1)                  UNIX Programmer's Manual                   TOUCH(1)

NAME
     touch - update date last modified of a file

SYNOPSIS
     touch [ -c ] file ...

DESCRIPTION
     Touch attempts to set the modified date of each file. This is done by
     reading a character from the file and writing it back.

     If a file does not exist, an attempt will be made to create it unless the
     -c option is specified.
  `
};

// Function to get a manual page for a command
export function getManPage(command: string): string | null {
  return manPages[command] || null;
}
