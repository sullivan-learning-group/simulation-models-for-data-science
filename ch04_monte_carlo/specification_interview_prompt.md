# Building a Simulation Specification with an LLM Interview

Simulation specifications should be precise and comprehensive. It is a good practice to use an LLM to help develop a set of requirements into a full specification. One approach is to create a prompt that combines as much detail as you have available with the simulation template and have the LLM interview you for additional detail. The following prompt is a starting point. Paste it into your LLM of choice, replacing the two bracketed sections with your own notes and the template from Appendix A.

```text
You are helping me write a Monte Carlo simulation specification. Your job is
to interview me, one section at a time, until every part of the attached
template is filled in with enough precision that a programmer (or an LLM)
could implement the simulation without asking me a single follow-up question.

WHAT I ALREADY KNOW

[Paste everything you have: the decision you are trying to make, the business
question as you currently understand it, any data you have (describe the
files, columns, date ranges, and sample sizes), known constraints, and any
distributions or parameters you have already estimated. Rough notes are
fine. If you have nothing for a section, say so.]

THE TEMPLATE

[Paste the full contents of monte_carlo_simulation_template.md here.]

HOW TO RUN THE INTERVIEW

1. Start by reading what I already know and mapping it onto the template.
   Tell me which sections you can fill in from my notes, which are partly
   covered, and which are empty. Do not start asking questions until you
   have shown me that map.

2. Work through the template in order: problem definition, input variables,
   dependencies, model logic, simulation settings, required outputs. Do not
   move to the next section until the current one is complete.

3. Ask no more than three questions at a time. Prefer one. Each question
   should target a specific field in the template, and you should say which
   field it fills.

4. Push back on vague answers. If I say "simulate revenue," ask what
   threshold, what time horizon, and what decision depends on the answer.
   If I give a distribution without a source, ask where the parameters came
   from. If I give a parameter without units, ask for units.

5. Never invent data. If I do not have historical data for an input, say so
   in the Source field and record my estimate as expert judgment. Label every
   assumption that rests on judgment rather than data so a reviewer can find
   them.

6. For every pair of input variables, ask whether they move together. If I
   am not sure, suggest how I could check (a correlation coefficient, a
   grouped comparison, a scatter plot) and record the dependency as
   "unverified" until I confirm it.

7. When the model logic is defined, do the hand-check with me: compute the
   expected value of the output from the mean of each input and compare it
   to the threshold in the business question. If the result looks
   implausible, tell me so before we go on.

8. Keep a running list of open items: anything I said I would look up,
   any assumption I flagged as uncertain, and any field still marked with a
   placeholder.

WHEN THE INTERVIEW IS COMPLETE

Produce the completed specification as a single markdown document that
follows the template exactly, with no bracketed placeholders remaining.
After the specification, add two short sections:

- Open items: the running list from step 8, so I know what still needs
  confirmation before the specification is trusted.
- Judgment calls: every parameter or assumption that came from my estimate
  rather than from data.

Do not generate any simulation code. That is a separate step and will use
this specification as its input.

Begin with step 1.
```

A few notes on why the prompt is shaped this way. The instruction to map the notes onto the template before asking anything keeps the LLM from asking questions you have already answered. The three-question limit keeps the interview conversational; an LLM left to its own devices will produce a twenty-item questionnaire that is easy to answer carelessly. The prohibition on inventing data matters most: LLMs are happy to supply a plausible-looking mean and standard deviation for a variable you never measured, and a fabricated parameter buried in a specification is much harder to catch than a blank one. Finally, keeping code generation out of this prompt separates the two jobs. The specification is a document you should read and sign off on before anything is built from it.
