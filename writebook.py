import os
import sys
import fire
import dotenv
import traceback
import time
import datetime

from source.openaiconnection import OpenAIConnection
from source.chain import ChainExecutor
from source.writelogs import WriteLogs
from source.bookchainelements import (
    WritePlot,
    FindBookTitle,
    WriteTableOfContents,
    WriteChapterSummaries,
    WriteChapterOutlines,
    WriteChapters,
    JoinBook
)

from source.oaa import (
    OAAControl,
    CreatePlot
)

# Load the environment variables.
dotenv.load_dotenv()

class ExitException(Exception):
    pass

def writebook(book_path, log=False, log_persistent=False, assistant=False, model="gpt-3.5-turbo"):

    # See if the book path exists. If not, raise an error.
    if not os.path.exists(book_path):
        raise ExitException(f"Path {book_path} does not exist. Please create it.")
    
    # See if the description.txt file exists. If not, raise an error.
    description_path = os.path.join(book_path, "description.txt")
    if not os.path.exists(description_path):
        raise ExitException(f"File {description_path} does not exist. Please create it. It should contain a short description of the book.")

    # Create the logger
    logger = WriteLogs(book_path, log=log, log_persistent=log_persistent)

    # Start time.
    start_time = time.time()

    # Create a chain executor.
    if not assistant:
        # Create the model connection.    
        model_connection = OpenAIConnection(logger)
    
        chain_executor = ChainExecutor(model_connection)
        #chain_executor.add_element(WritePlot(book_path)) # Experimental
        chain_executor.add_element(FindBookTitle(book_path))
        chain_executor.add_element(WriteTableOfContents(book_path))
        chain_executor.add_element(WriteChapterSummaries(book_path))
        chain_executor.add_element(WriteChapterOutlines(book_path))
        chain_executor.add_element(WriteChapters(book_path))
        chain_executor.add_element(JoinBook(book_path))
    else:
        # Create the connection and load history
        model_connection = OAAControl(book_path, logger, model)

        chain_executor = ChainExecutor(model_connection)
        chain_executor.add_element(CreatePlot(book_path))


    # Run the chain.
    chain_executor.run()

    # Elapsed time.
    elapsed_time = time.time() - start_time

    # Print the total number of tokens used.
    summary_file_path = os.path.join(book_path, "output", "summary.txt")
    with open(summary_file_path, "w") as summary_file:
        total_tokens_used = model_connection.get_token_count()
        print(f"Total tokens used: {total_tokens_used}", file=summary_file)

        elapsed_time_string = str(datetime.timedelta(seconds=elapsed_time))
        print(f"Elapsed time: {elapsed_time_string}", file=summary_file)


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        for i, arg in enumerate(args):
            if arg == '--l':
                args[i] = '--log=True'
            elif arg == '--lp':
                args[i] = '--log_persistent=True'
            elif arg == "--a":
                args[i] = "--assistant=True"
            elif (arg == "--m 4" or arg == "--m gpt4"):
                args[i] = "--model=gpt-4"
            elif (arg == "--m 3" or arg == "--m gpt3"):
                args[i] = "--model=gpt-3.5-turbo"
        print(args)
        fire.Fire(writebook, command=args)
    except ExitException as e:
        print(e)
    except:
        traceback.print_exc()

