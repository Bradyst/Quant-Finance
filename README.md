Project idea: [Investments]
	I will build a portfolio analysis risk analysis tool that uses historical market data to produce an objective analysis. The tool will present common risk metrics such as volatility, correlations, etc. The process will have the user give their portfolio data, and the returned will be a dashboard with the metrics calculated.

Who it is for:
	This software will be utilized by hopeful investors who want facts about the historical data of their portfolio to help with decisions for the future. This would be great for students looking for an easy and free tool to look at statistics and a beginner-friendly experience to portfolio management.

Data sources:
MAIN: Yahoo Finance API for historical stock data access and market benchmark data
I imagine minimal difficulty with accessing this data, but missing data would be a problem if encountered.

Major milestones (requirements):

Milestone 1 - Data collection✅
This step focuses on collecting portfolio information from a user, cleaning it, and computing basic statistics such as daily returns.

Milestone 2 - Risk analysis✅
Portfolio-level risk metrics are set up and calculated. Information such as volatility, correlations, and the Sharpe ratio will be returned to the user in some form.

Milestone 3 - UI polish
Ensure metrics and portfolio analysis are beginner-friendly, and each metric is explained. Potential charts can be viewed to visualize historical data to give meaning to the calculated numbers.

Finished product:
End-to-end functionality that prompts a user for portfolio information, returns relevant metrics, and gives explanations for each.

NOTE BEFORE RUNNING:
Ensure you are in the Quant-Finance directory in terminal before running the following commands.

TO RUN in terminal:
pip install -r requirements.txt
python app.py

TO RUN GUI:
pip install -r requirements.txt
python gui.py

The GUI will open another app on your desktop, click on this to view the GUI. It should be called python3.13.
