"""
Static definition of the Sparkle concept graph, spanning four subjects:
DSA, Python, SQL, and Machine Learning. One shared graph (not four separate
ones) so cross-subject prerequisites are possible later if needed, but in
practice edges stay within a subject for now.

`subject` on each concept is one of: "dsa" | "python" | "sql" | "ml".
"""

CONCEPTS = [
    # -- DSA --
    {"slug": "arrays", "name": "Arrays", "subject": "dsa", "difficulty_level": 1,
     "description": "Contiguous storage, indexing, traversal, and common array patterns."},
    {"slug": "strings", "name": "Strings", "subject": "dsa", "difficulty_level": 1,
     "description": "String manipulation, immutability, and common string algorithms."},
    {"slug": "hashing", "name": "Hashing", "subject": "dsa", "difficulty_level": 2,
     "description": "Hash maps/sets, collision handling, and O(1) average lookup patterns."},
    {"slug": "two-pointers", "name": "Two Pointers", "subject": "dsa", "difficulty_level": 2,
     "description": "Using two indices moving through a structure to avoid nested loops."},
    {"slug": "sliding-window", "name": "Sliding Window", "subject": "dsa", "difficulty_level": 3,
     "description": "Maintaining a moving window over a sequence for subarray/substring problems."},
    {"slug": "stack", "name": "Stack", "subject": "dsa", "difficulty_level": 2,
     "description": "LIFO structure -- parsing, monotonic stacks, backtracking support."},
    {"slug": "queue", "name": "Queue", "subject": "dsa", "difficulty_level": 2,
     "description": "FIFO structure -- BFS support, task scheduling patterns."},
    {"slug": "linked-list", "name": "Linked List", "subject": "dsa", "difficulty_level": 2,
     "description": "Node-based sequential structure -- traversal, reversal, cycle detection."},
    {"slug": "trees", "name": "Trees", "subject": "dsa", "difficulty_level": 3,
     "description": "Hierarchical structures -- traversals, BSTs, balancing."},
    {"slug": "graphs", "name": "Graphs", "subject": "dsa", "difficulty_level": 4,
     "description": "Vertices/edges, BFS/DFS, shortest paths, connectivity."},
    {"slug": "dynamic-programming", "name": "Dynamic Programming", "subject": "dsa", "difficulty_level": 5,
     "description": "Breaking problems into overlapping subproblems with memoization/tabulation."},

    # -- Python --
    {"slug": "py-syntax", "name": "Python Syntax", "subject": "python", "difficulty_level": 1,
     "description": "Core language syntax, data types, and control flow."},
    {"slug": "py-functions", "name": "Functions", "subject": "python", "difficulty_level": 1,
     "description": "Defining functions, arguments, scope, closures, decorators basics."},
    {"slug": "py-oop", "name": "OOP", "subject": "python", "difficulty_level": 2,
     "description": "Classes, inheritance, polymorphism, dunder methods."},
    {"slug": "py-file-handling", "name": "File Handling", "subject": "python", "difficulty_level": 2,
     "description": "Reading/writing files, context managers."},
    {"slug": "py-exceptions", "name": "Exception Handling", "subject": "python", "difficulty_level": 2,
     "description": "try/except/finally, custom exceptions, error propagation."},
    {"slug": "py-modules", "name": "Modules", "subject": "python", "difficulty_level": 2,
     "description": "Imports, packages, namespaces, project structure."},
    {"slug": "py-stdlib", "name": "Standard Library", "subject": "python", "difficulty_level": 3,
     "description": "collections, itertools, functools and other commonly used stdlib modules."},
    {"slug": "py-problem-solving", "name": "Problem Solving", "subject": "python", "difficulty_level": 3,
     "description": "Applying Python idiomatically to solve interview-style problems."},

    # -- SQL --
    {"slug": "sql-select", "name": "SELECT", "subject": "sql", "difficulty_level": 1,
     "description": "Basic querying, column selection, aliasing."},
    {"slug": "sql-where", "name": "WHERE", "subject": "sql", "difficulty_level": 1,
     "description": "Filtering rows with conditions, comparison and logical operators."},
    {"slug": "sql-group-by", "name": "GROUP BY", "subject": "sql", "difficulty_level": 2,
     "description": "Grouping rows for aggregate computation."},
    {"slug": "sql-order-by", "name": "ORDER BY", "subject": "sql", "difficulty_level": 1,
     "description": "Sorting result sets."},
    {"slug": "sql-joins", "name": "JOINs", "subject": "sql", "difficulty_level": 2,
     "description": "INNER/LEFT/RIGHT/FULL joins across tables."},
    {"slug": "sql-subqueries", "name": "Subqueries", "subject": "sql", "difficulty_level": 3,
     "description": "Nested queries, correlated vs uncorrelated subqueries."},
    {"slug": "sql-aggregations", "name": "Aggregations", "subject": "sql", "difficulty_level": 2,
     "description": "COUNT, SUM, AVG, MIN, MAX and HAVING."},
    {"slug": "sql-window-functions", "name": "Window Functions", "subject": "sql", "difficulty_level": 4,
     "description": "ROW_NUMBER, RANK, PARTITION BY, running totals."},
    {"slug": "sql-normalization", "name": "Normalization", "subject": "sql", "difficulty_level": 3,
     "description": "1NF/2NF/3NF, reducing redundancy in schema design."},
    {"slug": "sql-indexing", "name": "Indexing", "subject": "sql", "difficulty_level": 4,
     "description": "How indexes speed up lookups and their tradeoffs."},

    # -- Machine Learning --
    {"slug": "ml-linear-regression", "name": "Linear Regression", "subject": "ml", "difficulty_level": 1,
     "description": "Fitting a linear relationship, cost function, gradient descent basics."},
    {"slug": "ml-logistic-regression", "name": "Logistic Regression", "subject": "ml", "difficulty_level": 2,
     "description": "Binary classification via a sigmoid-linked linear model."},
    {"slug": "ml-regression", "name": "Regression (General)", "subject": "ml", "difficulty_level": 2,
     "description": "Regression techniques and metrics beyond simple linear regression."},
    {"slug": "ml-classification", "name": "Classification", "subject": "ml", "difficulty_level": 3,
     "description": "Classification algorithms and decision boundaries broadly."},
    {"slug": "ml-model-evaluation", "name": "Model Evaluation", "subject": "ml", "difficulty_level": 3,
     "description": "Choosing and interpreting evaluation metrics for a model."},
    {"slug": "ml-precision-recall", "name": "Accuracy / Precision / Recall", "subject": "ml", "difficulty_level": 3,
     "description": "Classification metrics and when each one matters."},
    {"slug": "ml-preprocessing", "name": "Preprocessing", "subject": "ml", "difficulty_level": 1,
     "description": "Cleaning, scaling, and encoding data before modeling."},
    {"slug": "ml-feature-engineering", "name": "Feature Engineering", "subject": "ml", "difficulty_level": 3,
     "description": "Creating and selecting features that improve model performance."},
    {"slug": "ml-train-test-split", "name": "Train/Test Split", "subject": "ml", "difficulty_level": 1,
     "description": "Splitting data for unbiased evaluation, validation sets, cross-validation."},
    {"slug": "ml-overfitting", "name": "Overfitting / Underfitting", "subject": "ml", "difficulty_level": 3,
     "description": "Bias-variance tradeoff and how to detect/fix over- or under-fitting."},
]

# (prerequisite_slug, dependent_slug, weight)
EDGES = [
    # DSA
    ("arrays", "two-pointers", 0.8),
    ("arrays", "sliding-window", 0.7),
    ("strings", "two-pointers", 0.6),
    ("hashing", "sliding-window", 0.5),
    ("arrays", "hashing", 0.5),
    ("arrays", "stack", 0.4),
    ("linked-list", "stack", 0.5),
    ("linked-list", "queue", 0.5),
    ("linked-list", "trees", 0.7),
    ("stack", "trees", 0.4),
    ("trees", "graphs", 0.8),
    ("queue", "graphs", 0.4),
    ("arrays", "dynamic-programming", 0.5),
    ("trees", "dynamic-programming", 0.4),
    ("graphs", "dynamic-programming", 0.3),

    # Python
    ("py-syntax", "py-functions", 0.9),
    ("py-functions", "py-oop", 0.8),
    ("py-functions", "py-file-handling", 0.6),
    ("py-functions", "py-exceptions", 0.7),
    ("py-oop", "py-modules", 0.5),
    ("py-modules", "py-stdlib", 0.6),
    ("py-oop", "py-problem-solving", 0.4),
    ("py-exceptions", "py-problem-solving", 0.3),
    ("py-stdlib", "py-problem-solving", 0.4),

    # SQL
    ("sql-select", "sql-where", 0.9),
    ("sql-where", "sql-group-by", 0.7),
    ("sql-group-by", "sql-order-by", 0.5),
    ("sql-group-by", "sql-aggregations", 0.8),
    ("sql-where", "sql-joins", 0.7),
    ("sql-joins", "sql-subqueries", 0.7),
    ("sql-aggregations", "sql-window-functions", 0.7),
    ("sql-joins", "sql-window-functions", 0.5),
    ("sql-select", "sql-normalization", 0.3),
    ("sql-normalization", "sql-indexing", 0.5),

    # ML
    ("ml-linear-regression", "ml-logistic-regression", 0.7),
    ("ml-linear-regression", "ml-regression", 0.6),
    ("ml-logistic-regression", "ml-classification", 0.8),
    ("ml-regression", "ml-model-evaluation", 0.5),
    ("ml-classification", "ml-model-evaluation", 0.6),
    ("ml-model-evaluation", "ml-precision-recall", 0.8),
    ("ml-preprocessing", "ml-feature-engineering", 0.7),
    ("ml-preprocessing", "ml-train-test-split", 0.5),
    ("ml-train-test-split", "ml-overfitting", 0.7),
    ("ml-model-evaluation", "ml-overfitting", 0.5),
]

# A handful of known misconception phrasings per concept, used by the
# embedding service to detect which misconception a student's free-text
# reasoning resembles. Not exhaustive -- covers the highest-value concepts
# first; extend as more question content is added.
MISCONCEPTIONS = {
    "hashing": ["a hash map looks up values in linear time same as a list"],
    "two-pointers": ["two pointers only works if the array is unsorted"],
    "sliding-window": ["the window size in sliding window is always fixed"],
    "trees": ["a binary search tree is the same thing as a balanced tree"],
    "graphs": ["depth first search always finds the shortest path"],
    "dynamic-programming": ["dynamic programming is just recursion with no memoization needed"],
    "py-oop": ["python does not support multiple inheritance"],
    "py-exceptions": ["a finally block only runs if an exception was raised"],
    "sql-joins": ["an inner join and a left join always return the same rows"],
    "sql-group-by": ["you can filter on an aggregate result using where instead of having"],
    "sql-window-functions": ["a window function collapses rows the same way group by does"],
    "ml-overfitting": ["a model with high training accuracy is always a good model"],
    "ml-precision-recall": ["accuracy is always the best metric regardless of class balance"],
    "ml-train-test-split": ["evaluating a model on its training data gives an unbiased estimate of performance"],
}
