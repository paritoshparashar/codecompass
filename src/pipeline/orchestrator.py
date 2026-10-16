class CodeCompassPipeline:

    # 0 - The application starts - 
    #   0.1 - Populates the domain objects 
    #          [Creates the repo - docs, and whatever we can do before receiving the issue - 
    #           create the settings and configs for the application to run ]
    # 1 - Receive the issue
    # 2 - Populates the issue domain object 
    # 2 - Calls the LocalizationService with the issue object [the repo can be accessed globally]
    #   2.1 - Select the strategy from the config file [BM25, BM25+Embeddings, Embeddings]
    # 3 - Receives the LocalizationResult
    # 4 - Calls the ClassifierService
    # 4 - Receives the ClassificationResult

    def __init__(self, classifier: IssueClassifier,
                 ranker: HybridRanker,
                 evluator: EvidenceEvaluator,
                 guide: GuideGenerator,
                 feedback: FeedbackController,
                 store: "RunStore"): ...

    def process(self, issue: Issue, config: Settings) -> RunReport:
    
        pass