
The project, "Grocery Store Association Rule Mining with Apriori Algorithm," utilizes the Apriori algorithm to analyze a grocery dataset and uncover patterns in customer purchasing behavior. The script identifies frequent itemsets, representing items commonly bought together, and generates association rules based on support, confidence, and lift metrics.

Key features of the project include the ability to customize support and confidence thresholds, providing flexibility for users. The output includes both frequent itemsets and association rules that exceed the specified thresholds. These results offer insights into customer preferences, aiding decisions related to product placement, bundling, and marketing strategies in the retail sector.

The project emphasizes the significance of metrics such as support, confidence, and lift in filtering and prioritizing meaningful patterns. The documentation provides usage instructions, examples, and a contribution guide for collaboration. The code is released under a specified license, and acknowledgments are given to external contributions.

Future work considerations involve potential enhancements and additional features to improve the script's functionality. Overall, the project serves as a valuable tool for retailers seeking actionable insights from grocery transactional data.

My PCY algorithm produced the same output as the Apriori algorithm, but the thing is it was faster than the apriori algorithm. It computed
the correct algorithm in less than 10 seconds, while my Apriori algorithm took a lot of time to compute the frequent itemsets and much more time to get the confidence of each association rule.

This hash-based methods helps PCY scale better to large datasets and improves its runtime efficiency in comparison to Apriori, 
particularly when dealing with sparse datasets where most itemsets are infrequent. 
