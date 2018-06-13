# Copyright (c) 2018 by Dmitry Odintsov
# This code is licensed under the MIT license (MIT)
# (http://opensource.org/licenses/MIT)

# Segment class module

import os

from . import Utils

class Segment():
    """ Contains information about transport segment """

    def __init__(self, id, url, stream):
        self.id = id
        self.url = url
        self.stream = stream

    def __lt__(self, rhs):
        if self.stream is None:
            return False
        elif rhs.stream is None:
            return True
        else:
            return self.id < rhs.id if self.stream == rhs.stream else self.stream < rhs.stream

    def __eq__(self, rhs):
        return False if rhs is None else (self.stream == rhs.stream and self.id == rhs.id)

    def tsFilepath(self):
        return os.path.join(self.stream.root, Utils.TS_DIR, '{id}.ts'.format(id = self.id))

    def tcFilepath(self):
        return os.path.join(self.stream.root, Utils.TC_DIR, '{id}.mp4'.format(id = self.id))

    def concatFilepath(self):
        return os.path.join(self.stream.root, '{id}.ts'.format(id = self.id))

    def stdoutFilepath(self):
        return os.path.join(self.stream.root, Utils.LOG_DIR, '{id}_out.txt'.format(id = self.id))

    def stderrFilepath(self):
        return os.path.join(self.stream.root, Utils.LOG_DIR, '{id}_err.txt'.format(id = self.id))

    def checkSubprocess(self, proc):
        exit_code = proc.returncode

        if exit_code is not 0:
            out, err = proc.communicate()
            with open(self.stdoutFilepath(), 'a') as f:
                f.write('========\n')
                f.write(str(out, 'utf-8'))
                f.write('========\n')

            with open(self.stderrFilepath(), 'a') as f:
                f.write('========\n')
                f.write(str(err, 'utf-8'))
                f.write('========\n')


    def __str__(self):
        return 'Segment {{ {id}, {url}, {stream} }}'.format(id = self.id, url = self.url, stream = self.stream)
