class settings(object):
    # Get the root directory for saving messages
    DATA_DIR = 'tools_edi_as2/data_edi'

    # Max number of times to retry failed sends
    MAX_RETRIES = 5

    # URL for receiving asynchronous MDN from partners
    MDN_URL = "http://localhost:8070/as2receive"

    # Max time to wait for asynchronous MDN in minutes
    ASYNC_MDN_WAIT = 30

    # Max number of days worth of messages to be saved in archive
    MAX_ARCH_DAYS =30