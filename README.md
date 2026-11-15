# Simulation Models for Data Science: Companion Files

This repository holds the companion files for *Simulation Models for Data Science* by Dan Sullivan (O'Reilly). It contains the specification templates, the completed coffee shop examples, the generated Python scripts, and the data used in the book.

The book uses specification-driven development: you describe a simulation in a structured specification, use an LLM to generate code from that specification, and then validate the results. Each folder below contains the blank templates for one modeling technique, along with completed versions for the book's running coffee shop example.

## Contents

| Folder | Chapter | What's inside |
|---|---|---|
| [`ch04_monte_carlo/`](ch04_monte_carlo/) | Chapter 4: Using Monte Carlo Simulation to Model Uncertainty in Decision Making (Appendix A) | Monte Carlo specification template, specification interview prompt, coffee shop data and codebook, simulation and data validation scripts, simulation results |
| [`ch05_discrete_event_simulation/`](ch05_discrete_event_simulation/) | Chapter 5: Finding and Fixing Process Bottlenecks with Discrete Event Simulation (Appendix B) | DES Templates A–C, completed coffee shop staffing specifications A–C, generated SimPy script |
| [`ch06_system_dynamics/`](ch06_system_dynamics/) | Chapter 6: System dynamics (Appendix C) | System dynamics Templates A–C and completed coffee shop versions |
| [`ch07_agent_based_modeling/`](ch07_agent_based_modeling/) | Chapter 7: Agent-based modeling (Appendix D) | Agent-based modeling Templates A–C and completed coffee shop versions |
| [`ch11_communicating_results/`](ch11_communicating_results/) | Chapter 11: Driving adoption and action from simulation insights | Results and recommendations template; Monte Carlo dashboards built with Dash, Panel, and Streamlit |

### The three templates

Each modeling technique (DES, system dynamics, and agent-based modeling) uses three templates:

- **Template A** specifies the model: the business question, the structure of the system, the inputs and their distributions, and the scenarios to compare.
- **Template B** is the code generation prompt you give an LLM, with your completed Template A embedded in it.
- **Template C** lists the validation checks to run on the results and the structure for summarizing what you found.

The Monte Carlo chapter uses a single specification template, along with an interview prompt that has an LLM help you fill it in.

## Running the code

The scripts need Python 3.10 or later. Install the dependencies with:

```bash
pip install -r requirements.txt
```

Then run a script from its own folder, for example:

```bash
cd ch05_discrete_event_simulation
python coffee_shop_des.py
```

The scripts write their plots and results files to the folder you run them from.

## License

The code, templates, and data in this repository are released under the [MIT License](LICENSE). The text of the book is copyright O'Reilly Media and is not included here.
