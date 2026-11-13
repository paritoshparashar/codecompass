from code_compass.adapters.cli import CLIAdapter
from code_compass.logger import Logger
from code_compass.pipeline.orchestrator import CodeCompassPipeline
from code_compass.pipeline.workflow import CodeCompassWorkflow


def main():

    Logger.log_start("Welcome to Code Compass!")

    pipeline = CodeCompassPipeline()
    # Create the Adapter, which implements the (Port)UserInteractionPort interface
    adapter = CLIAdapter()

    # Create the Application, which uses the pipeline and the adapter
    application = CodeCompassWorkflow(
        pipeline=pipeline,
        inputPort=adapter,  # attach the adapter to the port
    )

    application.run()
    Logger.log_end("CodeCompass Exited")


if __name__ == "__main__":
    main()
