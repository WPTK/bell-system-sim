import { useState, useEffect } from "react";

interface ManualPanelProps {
  selectedCommand: string | null;
  onClose: () => void;
}

interface ManualPage {
  name: string;
  synopsis: string;
  description: string;
  options?: { flag: string; description: string }[];
  examples?: string[];
}

const manualPages: Record<string, ManualPage> = {
  ls: {
    name: "ls - list contents of directory",
    synopsis: "ls [ -acdilrstu ] [ name... ]",
    description: "For each directory argument, ls lists the contents of the directory; for each file argument, ls repeats its name and any other information requested. When no argument is given, the current directory is listed.",
    options: [
      { flag: "-a", description: "List all entries; in the absence of this option, entries whose names begin with a period are not listed." },
      { flag: "-c", description: "Use time of last modification of the i-node for sorting or printing." },
      { flag: "-d", description: "If argument is a directory, list only its name, not its contents." },
      { flag: "-i", description: "Print i-number in first column of the report." },
      { flag: "-l", description: "List in long format, giving mode, number of links, owner, size in bytes, and time of last modification." },
      { flag: "-r", description: "Reverse the order of sort to get reverse alphabetic or oldest first." },
      { flag: "-s", description: "Give size in blocks for each entry." },
      { flag: "-t", description: "Sort by time modified instead of by name." },
      { flag: "-u", description: "Use time of last access instead of last modification for sorting or printing." },
    ],
    examples: ["ls", "ls -la", "ls -lt /etc"]
  },
  cat: {
    name: "cat - concatenate and print files",
    synopsis: "cat [ -u ] file...",
    description: "Cat reads each file in sequence and displays it on the standard output. Thus 'cat file' displays the file and 'cat file1 file2' concatenates the files and displays the result.",
    options: [
      { flag: "-u", description: "Make output completely unbuffered." },
    ],
    examples: ["cat file.txt", "cat file1 file2", "cat -u /etc/motd"]
  },
  ps: {
    name: "ps - process status",
    synopsis: "ps [ alx ] [ namelist ]",
    description: "Ps prints information about active processes. Without options, information is printed about processes associated with the controlling terminal.",
    options: [
      { flag: "a", description: "Include information about processes owned by others." },
      { flag: "l", description: "Long listing." },
      { flag: "x", description: "Include processes not associated with a terminal." },
    ],
    examples: ["ps", "ps -al", "ps -ax"]
  },
  who: {
    name: "who - who is on the system",
    synopsis: "who [ who-file ] [ am i ]",
    description: "Who, without an argument, lists the login name, terminal name, and login time for each current user.",
    examples: ["who", "who am i"]
  },
  grep: {
    name: "grep - search a file for a pattern",
    synopsis: "grep [ -v ] [ -c ] [ -n ] pattern [ file... ]",
    description: "Grep searches the input files for lines containing a match to the given pattern. By default, grep prints the matching lines.",
    options: [
      { flag: "-v", description: "Print all lines except those that contain the pattern." },
      { flag: "-c", description: "Print only a count of matching lines." },
      { flag: "-n", description: "Print each matching line preceded by its line number." },
    ],
    examples: ["grep 'hello' file.txt", "grep -n 'pattern' *.c", "grep -v 'exclude' data.txt"]
  },
  cp: {
    name: "cp - copy files",
    synopsis: "cp file1 file2",
    description: "Cp copies the contents of file1 onto file2. The mode and owner of file2 are preserved if it already existed; the mode of the source file is used otherwise.",
    examples: ["cp source.txt dest.txt", "cp file /tmp/"]
  },
  mv: {
    name: "mv - move or rename files",
    synopsis: "mv file1 file2",
    description: "Mv moves (renames) file1 to file2. If file2 already exists, it is removed before file1 is renamed.",
    examples: ["mv old.txt new.txt", "mv file /tmp/"]
  },
  rm: {
    name: "rm - remove files",
    synopsis: "rm [ -f ] [ -i ] [ -r ] file...",
    description: "Rm removes the entries for one or more files from a directory. If an entry was the last link to the file, the file is destroyed.",
    options: [
      { flag: "-f", description: "Remove files without prompting for confirmation." },
      { flag: "-i", description: "Interactive mode; confirm before removing each file." },
      { flag: "-r", description: "Recursively remove directories and their contents." },
    ],
    examples: ["rm file.txt", "rm -i *.tmp", "rm -rf directory/"]
  },
  pwd: {
    name: "pwd - print working directory",
    synopsis: "pwd",
    description: "Pwd prints the pathname of the working (current) directory.",
    examples: ["pwd"]
  },
  date: {
    name: "date - print date and time",
    synopsis: "date",
    description: "Date prints the current date and time.",
    examples: ["date"]
  },
  man: {
    name: "man - print manual pages",
    synopsis: "man [ section ] title",
    description: "Man locates and prints the named title from the system manual. The optional section number restricts the search to that section of the manual.",
    examples: ["man ls", "man 1 ps", "man grep"]
  }
};

const commandsList = [
  "awk", "cat", "cd", "chmod", "cp", "diff", "echo", "ed", "find", "grep",
  "ls", "make", "man", "mkdir", "mv", "ps", "pwd", "rm", "sed", "sh",
  "sort", "wc", "who", "write"
];

export default function ManualPanel({ selectedCommand, onClose }: ManualPanelProps) {
  const [currentPage, setCurrentPage] = useState<string>(selectedCommand || "ls");
  const [activeTab, setActiveTab] = useState<"manual" | "commands" | "history" | "files">("manual");

  useEffect(() => {
    if (selectedCommand) {
      setCurrentPage(selectedCommand);
      setActiveTab("manual");
    }
  }, [selectedCommand]);

  const manual = manualPages[currentPage];

  return (
    <div className="w-1/3 border-l border-terminal-green bg-crt-dark overflow-y-auto">
      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-300">
        <div className="flex">
          {(["manual", "commands", "history", "files"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-serif text-xs border-r border-gray-300 capitalize ${
                activeTab === tab
                  ? "bg-amber text-black font-bold"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              {tab}
            </button>
          ))}
          <button
            onClick={onClose}
            className="ml-auto px-4 py-2 text-gray-600 hover:bg-gray-100 font-serif text-xs"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === "manual" && (
          <>
            <div className="text-center mb-6">
              <h2 className="font-serif text-lg font-bold text-terminal-green">THE BELL SYSTEM</h2>
              <h3 className="font-serif text-base font-bold text-terminal-green">TECHNICAL JOURNAL</h3>
              <p className="text-xs mt-2 text-phosphor">UNIX Programmer's Manual</p>
              <p className="text-xs text-phosphor">Seventh Edition, Volume 1</p>
              <p className="text-xs text-gray-400">January 1979</p>
            </div>

            {manual ? (
              <div className="bg-white p-3 border border-gray-300 font-mono text-xs text-black">
                <div className="font-bold text-terminal-amber bg-black p-1 mb-2">
                  {currentPage.toUpperCase()}(1)
                </div>
                
                <div className="mb-4">
                  <div className="font-bold">NAME</div>
                  <div className="ml-4">{manual.name}</div>
                </div>
                
                <div className="mb-4">
                  <div className="font-bold">SYNOPSIS</div>
                  <div className="ml-4">{manual.synopsis}</div>
                </div>
                
                <div className="mb-4">
                  <div className="font-bold">DESCRIPTION</div>
                  <div className="ml-4">{manual.description}</div>
                </div>
                
                {manual.options && (
                  <div className="mb-4">
                    <div className="font-bold">OPTIONS</div>
                    <div className="ml-4">
                      {manual.options.map((option, index) => (
                        <div key={index} className="mb-1">
                          <span className="font-bold">{option.flag}</span> - {option.description}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {manual.examples && (
                  <div>
                    <div className="font-bold">EXAMPLES</div>
                    <div className="ml-4">
                      {manual.examples.map((example, index) => (
                        <div key={index} className="font-mono bg-gray-100 p-1 mb-1">
                          {example}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white p-3 border border-gray-300 text-xs text-black">
                <div className="text-red-500">Manual page for '{currentPage}' not found.</div>
              </div>
            )}
          </>
        )}

        {activeTab === "commands" && (
          <div className="border-b border-gray-300 pb-4">
            <h4 className="font-serif font-bold mb-2 text-terminal-green">SECTION I - COMMANDS</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {commandsList.map((cmd) => (
                <div
                  key={cmd}
                  className="hover:bg-yellow-100 hover:text-black p-1 cursor-pointer text-phosphor"
                  onClick={() => {
                    setCurrentPage(cmd);
                    setActiveTab("manual");
                  }}
                >
                  {cmd}(1)
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "history" && (
          <div>
            <h4 className="font-serif font-bold mb-2 text-terminal-green">COMMAND HISTORY</h4>
            <div className="bg-white p-3 border border-gray-300 text-xs text-black">
              <div className="text-gray-500">Command history will appear here...</div>
            </div>
          </div>
        )}

        {activeTab === "files" && (
          <div>
            <h4 className="font-serif font-bold mb-2 text-terminal-green">SYSTEM STATUS</h4>
            <div className="bg-white p-3 border border-gray-300 text-xs text-black">
              <div className="flex justify-between">
                <span>System:</span>
                <span className="font-mono">UNIX V7</span>
              </div>
              <div className="flex justify-between">
                <span>Machine:</span>
                <span className="font-mono">PDP-11/70</span>
              </div>
              <div className="flex justify-between">
                <span>Users:</span>
                <span className="font-mono">3</span>
              </div>
              <div className="flex justify-between">
                <span>Load:</span>
                <span className="font-mono">0.23</span>
              </div>
              <div className="flex justify-between">
                <span>Uptime:</span>
                <span className="font-mono">2 days</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
