

class OutputLog(object):
    """Output messages and errors are stored in this object and can be recalled
    when creating widgets that need to show the history of messages and errros."""

    def __init__(self):
        super(OutputLog, self).__init__()
        self._outputLog = ""


    def write(self, text):
        self._outputLog += str(text)


    def getLog(self):
        """Gets the logged output to this point.

        Returns:
            str: Logged output.

        """

        return self._outputLog