"""
Hardcoded math concept library (Phase 1 MVP).

Concepts are organized as individual "practice targets" with prerequisite
tracking and sample step-by-step solutions.
"""

from __future__ import annotations

from typing import Any

from concepts.prerequisites import get_prerequisites as _get_prerequisites
from concepts.prerequisites import recommend_next_concepts as _recommend_next_concepts


def _make_sample(
    *,
    problem_statement: str,
    steps: list[str],
    answer: str,
    common_mistakes: list[str],
) -> dict[str, Any]:
    return {
        "problem_statement": problem_statement,
        "steps": steps,
        "answer": answer,
        "common_mistakes": common_mistakes,
    }


CONCEPTS: dict[str, dict[str, Any]] = {
    # Algebra
    "algebra_linear_equations": {
        "id": "algebra_linear_equations",
        "name": "Linear Equations (1 variable)",
        "category": "Algebra",
        "description": "Solve equations of the form ax + b = c with step-by-step transformations.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve for x: 2x + 3 = 11",
                    steps=["2x = 8", "x = 4"],
                    answer="x=4",
                    common_mistakes=[
                        "Subtract 3 but forget to apply it to both sides",
                        "Divide incorrectly (e.g., x=8 instead of x=4)",
                    ],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve for x: 5x - 7 = 3",
                    steps=["5x = 10", "x = 2"],
                    answer="x=2",
                    common_mistakes=["Sign error when moving -7", "Arithmetic error after dividing"],
                ),
            },
        ],
    },
    "algebra_quadratic_equations": {
        "id": "algebra_quadratic_equations",
        "name": "Quadratic Equations (factoring)",
        "category": "Algebra",
        "description": "Solve quadratics by factoring into (x-r)(x-s)=0 and finding roots.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve for x: x^2 - 5x + 6 = 0",
                    steps=["x^2 - 5x + 6 = (x-2)(x-3)", "(x-2)(x-3)=0", "x=2", "x=3"],
                    answer="x=2 or x=3",
                    common_mistakes=["Forgetting to set each factor equal to 0", "Expanding factors incorrectly"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve for x: x^2 + 4x + 3 = 0",
                    steps=["x^2 + 4x + 3 = (x+1)(x+3)", "(x+1)(x+3)=0", "x=-1", "x=-3"],
                    answer="x=-1 or x=-3",
                    common_mistakes=["Mixing up signs on the factors", "Not including both roots"],
                ),
            },
        ],
    },
    "algebra_systems_equations": {
        "id": "algebra_systems_equations",
        "name": "Systems of Equations (elimination)",
        "category": "Algebra",
        "description": "Solve two linear equations in x and y using elimination with clear arithmetic steps.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve the system: x + y = 7 and x - y = 1",
                    steps=["2x = 8", "x = 4", "y = 3"],
                    answer="(x,y)=(4,3)",
                    common_mistakes=["Adding/subtracting incorrectly to eliminate y", "Substitution arithmetic errors"],
                ),
            }
        ],
    },
    "algebra_factoring": {
        "id": "algebra_factoring",
        "name": "Factoring Quadratics",
        "category": "Algebra",
        "description": "Factor quadratics by finding two numbers that multiply and add to the required terms.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Factor: x^2 - 5x + 6",
                    steps=["x^2 - 5x + 6 = (x-2)(x-3)", "(x-2)(x-3)"],
                    answer="(x-2)(x-3)",
                    common_mistakes=["Incorrect factor pair", "Wrong signs in the parentheses"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Factor: x^2 + 2x - 8",
                    steps=["x^2 + 2x - 8 = (x+4)(x-2)", "(x+4)(x-2)"],
                    answer="(x+4)(x-2)",
                    common_mistakes=["Using factors that multiply to c but don't add to b", "Forgetting order signs"],
                ),
            },
        ],
    },
    # Calculus
    "calculus_limits": {
        "id": "calculus_limits",
        "name": "Evaluating Limits",
        "category": "Calculus",
        "description": "Evaluate simple limits using direct substitution and basic algebra.",
        "available_difficulties": ["beginner"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Evaluate: lim_{x->2} (x^2)",
                    steps=["2^2", "4"],
                    answer="4",
                    common_mistakes=["Substituting incorrectly (e.g., x= -2)", "Arithmetic errors squaring"],
                ),
            }
        ],
    },
    "calculus_derivatives": {
        "id": "calculus_derivatives",
        "name": "Derivatives (power rule)",
        "category": "Calculus",
        "description": "Differentiate polynomials using the power rule and simplify.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find the derivative of f(x)=x^3",
                    steps=["f'(x)=3x^2"],
                    answer="3x^2",
                    common_mistakes=["Forgetting to multiply by the exponent", "Exponent error (x^3 -> x^3 instead of x^2)"],
                ),
            }
        ],
    },
    "calculus_integrals": {
        "id": "calculus_integrals",
        "name": "Integrals (power rule)",
        "category": "Calculus",
        "description": "Compute basic integrals of polynomials and append the constant of integration.",
        "available_difficulties": ["intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Compute: ∫ x dx",
                    steps=["x^2/2", "x^2/2 + C"],
                    answer="x^2/2 + C",
                    common_mistakes=["Using the derivative rule instead of the integral rule", "Forgetting +C"],
                ),
            },
            {
                "difficulty": "advanced",
                **_make_sample(
                    problem_statement="Compute: ∫ (2x^3) dx",
                    steps=["(2)*(x^4/4)", "x^4/2 + C"],
                    answer="x^4/2 + C",
                    common_mistakes=["Not dividing by the new exponent", "Algebra mistake simplifying constants"],
                ),
            },
        ],
    },
    # Geometry
    "geometry_area": {
        "id": "geometry_area",
        "name": "Area of Rectangles/Shapes",
        "category": "Geometry",
        "description": "Calculate areas using multiplication and basic geometric formulas.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find area of a rectangle: length 5, width 3",
                    steps=["A = 5*3", "A = 15"],
                    answer="15",
                    common_mistakes=["Multiplying the wrong sides", "Sign/units confusion"],
                ),
            }
        ],
    },
    "geometry_volume": {
        "id": "geometry_volume",
        "name": "Volume of Rectangular Prisms",
        "category": "Geometry",
        "description": "Calculate volume as length*width*height with clear arithmetic steps.",
        "available_difficulties": ["beginner"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find volume of a prism: l=2, w=3, h=4",
                    steps=["V = 2*3*4", "V = 24"],
                    answer="24",
                    common_mistakes=["Forgetting one dimension", "Arithmetic errors"],
                ),
            }
        ],
    },
    "geometry_pythagorean": {
        "id": "geometry_pythagorean",
        "name": "Pythagorean Theorem",
        "category": "Geometry",
        "description": "Use a^2 + b^2 = c^2 to solve for missing right-triangle sides.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Use the Pythagorean theorem: a=3, b=4. Find c.",
                    steps=["c^2 = 3^2 + 4^2", "c^2 = 25", "c = 5"],
                    answer="5",
                    common_mistakes=["Forgetting to square a and b", "Taking the square root incorrectly"],
                ),
            }
        ],
    },
    # Trigonometry
    "trigonometry_basic": {
        "id": "trigonometry_basic",
        "name": "Basic Trig Values",
        "category": "Trigonometry",
        "description": "Evaluate common special-angle trig functions (sin/cos) as exact values.",
        "available_difficulties": ["beginner"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find sin(30°) as an exact value.",
                    steps=["sin(30°)=1/2", "1/2"],
                    answer="1/2",
                    common_mistakes=["Using the wrong special-angle table value", "Answering with a decimal instead of exact fraction"],
                ),
            }
        ],
    },
    "trigonometry_unit_circle": {
        "id": "trigonometry_unit_circle",
        "name": "Unit Circle Coordinates",
        "category": "Trigonometry",
        "description": "Use the unit circle to read exact sine/cosine values for key angles.",
        "available_difficulties": ["beginner", "intermediate"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find cos(pi/3) as an exact value.",
                    steps=["cos(pi/3)=1/2", "1/2"],
                    answer="1/2",
                    common_mistakes=["Confusing sin and cos", "Wrong sign for quadrant"],
                ),
            }
        ],
    },
    "trigonometry_identities": {
        "id": "trigonometry_identities",
        "name": "Trigonometric Identities",
        "category": "Trigonometry",
        "description": "Simplify expressions using fundamental trig identities.",
        "available_difficulties": ["intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Simplify: sin(x)^2 + cos(x)^2",
                    steps=["sin(x)^2 + cos(x)^2 = 1", "1"],
                    answer="1",
                    common_mistakes=["Using an incorrect identity sign", "Not squaring both trig functions"],
                ),
            }
        ],
    },
    # Applied Math / Finance
    "applied_simple_interest": {
        "id": "applied_simple_interest",
        "name": "Applications of Simple Interest",
        "category": "Applied Math",
        "description": "Use I = P*r*t and A = P + I to compute interest and final amount.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find interest and final amount for P=1000, r=0.05, t=3.",
                    steps=["I = 1000*0.05*3", "I = 150", "A = 1000 + 150", "A = 1150"],
                    answer="I=150, A=1150",
                    common_mistakes=["Using 5 instead of 0.05 for the rate", "Forgetting to add interest to principal"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Find A for P=2400, r=0.0375, t=4.",
                    steps=["I = 2400*0.0375*4", "I = 360", "A = 2400 + 360", "A = 2760"],
                    answer="A=2760",
                    common_mistakes=["Decimal multiplication error", "Using t in months instead of years"],
                ),
            },
        ],
    },
    "applied_compound_interest": {
        "id": "applied_compound_interest",
        "name": "Applications of Compound Interest",
        "category": "Applied Math",
        "description": "Use A = P(1 + r/n)^(n*t) and continuous compounding formulas.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Compute A for P=1000, r=0.05, n=12, t=3.",
                    steps=["A = 1000*(1+0.05/12)^(12*3)", "A = 1000*(1.0041667)^36", "A ≈ 1161.47"],
                    answer="1161.47",
                    common_mistakes=["Forgetting to multiply n*t in the exponent", "Using simple interest formula by mistake"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Find continuous-compound amount for P=1500, r=0.04, t=5.",
                    steps=["A = 1500*e^(0.04*5)", "A = 1500*e^0.2", "A ≈ 1832.10"],
                    answer="1832.10",
                    common_mistakes=["Using (1+r)^t instead of e^(rt)", "Exponent arithmetic error"],
                ),
            },
        ],
    },
    "applied_distance_rate_time": {
        "id": "applied_distance_rate_time",
        "name": "Applications for Distance",
        "category": "Applied Math",
        "description": "Solve d=rt, r=d/t, and t=d/r problems with units.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Travel 120 miles in 2 hours. Find speed.",
                    steps=["r = d/t", "r = 120/2", "r = 60"],
                    answer="60 mph",
                    common_mistakes=["Swapping distance and time", "Dropping units"],
                ),
            }
        ],
    },
    "applied_mixture": {
        "id": "applied_mixture",
        "name": "Applications for Mixture",
        "category": "Applied Math",
        "description": "Set up and solve concentration/value mixture equations.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Mix 2 L of 30% acid with 3 L of 50% acid. Find final concentration.",
                    steps=["acid = 0.3*2 + 0.5*3", "acid = 2.1", "concentration = 2.1/5", "concentration = 0.42"],
                    answer="42%",
                    common_mistakes=["Adding percentages directly", "Using wrong total volume"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="How many liters of 20% solution are needed to mix with 4 L of 50% to get 32%?",
                    steps=["0.2x + 0.5*4 = 0.32*(x+4)", "0.2x + 2 = 0.32x + 1.28", "0.72 = 0.12x", "x = 6"],
                    answer="6 liters",
                    common_mistakes=["Wrong distribution on right side", "Sign error when isolating x"],
                ),
            },
        ],
    },
    # Algebra / Precalculus extensions
    "algebra_functions_relations": {
        "id": "algebra_functions_relations",
        "name": "Functions and Relations",
        "category": "Algebra",
        "description": "Distinguish relations from functions using ordered pairs and the vertical line test.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Is {(1,2), (1,3), (2,4)} a function?",
                    steps=["x=1 maps to 2 and 3", "one x has two outputs", "not a function"],
                    answer="Not a function",
                    common_mistakes=["Checking repeated y-values instead of x-values", "Assuming any set of pairs is a function"],
                ),
            }
        ],
    },
    "algebra_linear_two_variables": {
        "id": "algebra_linear_two_variables",
        "name": "Linear Equations in Two Variables",
        "category": "Algebra",
        "description": "Rewrite ax+by=c into slope-intercept form and identify slope/intercept.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Rewrite 2x + 3y = 6 in slope-intercept form.",
                    steps=["3y = -2x + 6", "y = (-2/3)x + 2"],
                    answer="y = (-2/3)x + 2",
                    common_mistakes=["Dividing only one term by 3", "Sign error moving 2x"],
                ),
            }
        ],
    },
    "algebra_linear_functions": {
        "id": "algebra_linear_functions",
        "name": "Linear Functions",
        "category": "Algebra",
        "description": "Identify slope and intercept in f(x)=mx+b and build linear models.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="For f(x)=2x-3, identify slope and y-intercept.",
                    steps=["m = 2", "b = -3"],
                    answer="slope=2, y-intercept=-3",
                    common_mistakes=["Swapping m and b", "Dropping the negative sign"],
                ),
            }
        ],
    },
    "algebra_rational_equations": {
        "id": "algebra_rational_equations",
        "name": "Linear and Rational Equations",
        "category": "Algebra",
        "description": "Solve equations with denominators using LCD and check extraneous roots.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve 3/(x-2)=5.",
                    steps=["3 = 5*(x-2)", "3 = 5x - 10", "13 = 5x", "x = 13/5"],
                    answer="x=13/5",
                    common_mistakes=["Incorrect distribution", "Forgetting denominator restrictions"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve 2/x + 1 = 5/3.",
                    steps=["2/x = 2/3", "6 = 2x", "x = 3"],
                    answer="x=3",
                    common_mistakes=["LCD multiplication errors", "Not checking x ≠ 0"],
                ),
            },
        ],
    },
    "algebra_absolute_value_equations": {
        "id": "algebra_absolute_value_equations",
        "name": "Absolute Value Equations",
        "category": "Algebra",
        "description": "Solve |ax+b|=c by splitting into two linear equations when c>0.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve |2x-1|=5.",
                    steps=["2x-1 = 5 or 2x-1 = -5", "x = 3 or x = -2"],
                    answer="x=3 or x=-2",
                    common_mistakes=["Solving only one branch", "Sign errors in second branch"],
                ),
            }
        ],
    },
    "algebra_absolute_value_inequalities": {
        "id": "algebra_absolute_value_inequalities",
        "name": "Linear, Compound, and Absolute Value Inequalities",
        "category": "Algebra",
        "description": "Solve and graph linear/compound/absolute value inequalities.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Solve |x-2| < 3.",
                    steps=["-3 < x-2 < 3", "-1 < x < 5"],
                    answer="-1 < x < 5",
                    common_mistakes=["Using OR instead of AND for < case", "Forgetting to shift both bounds"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve |2x+1| > 7.",
                    steps=["2x+1 > 7 or 2x+1 < -7", "x > 3 or x < -4"],
                    answer="x>3 or x<-4",
                    common_mistakes=["Using AND instead of OR for > case", "Division/sign errors"],
                ),
            },
        ],
    },
    "precalculus_graph_transformations": {
        "id": "precalculus_graph_transformations",
        "name": "Transformation of Graphs",
        "category": "Precalculus",
        "description": "Interpret y = a*f(b(x-h))+k as stretches/reflections/shifts.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Describe transformations from f(x)=sqrt(x) to g(x)=2*sqrt(x-3)+1.",
                    steps=["vertical stretch by 2", "shift right 3", "shift up 1"],
                    answer="stretch 2, right 3, up 1",
                    common_mistakes=["Wrong sign on horizontal shift", "Confusing stretch/compression factors"],
                ),
            }
        ],
    },
    "precalculus_piecewise_analysis": {
        "id": "precalculus_piecewise_analysis",
        "name": "Analyzing Graphs and Piecewise Functions",
        "category": "Precalculus",
        "description": "Analyze domain/range/interval behavior and piecewise definitions.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="For f(x)=x^2 if x<0 and f(x)=2x if x>=0, find f(-2) and f(3).",
                    steps=["f(-2)=(-2)^2=4", "f(3)=2*3=6"],
                    answer="f(-2)=4, f(3)=6",
                    common_mistakes=["Using wrong branch for x value", "Not applying piecewise condition"],
                ),
            }
        ],
    },
    "algebra_function_operations": {
        "id": "algebra_function_operations",
        "name": "Algebra of Functions",
        "category": "Algebra",
        "description": "Compute (f+g), (f-g), (f*g), and (f/g) with domain restrictions.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Given f(x)=x^2 and g(x)=x+1, find (f+g)(x).",
                    steps=["(f+g)(x)=f(x)+g(x)", "(f+g)(x)=x^2+x+1"],
                    answer="x^2+x+1",
                    common_mistakes=["Multiplying instead of adding functions", "Dropping terms"],
                ),
            }
        ],
    },
    "algebra_function_composition": {
        "id": "algebra_function_composition",
        "name": "Function Composition",
        "category": "Algebra",
        "description": "Compute f(g(x)) and understand order sensitivity.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="If f(x)=x^2 and g(x)=x+1, find f(g(x)).",
                    steps=["f(g(x)) = (x+1)^2", "(x+1)^2 = x^2+2x+1"],
                    answer="x^2+2x+1",
                    common_mistakes=["Doing composition in wrong order", "Squaring incorrectly"],
                ),
            }
        ],
    },
    "algebra_complex_numbers": {
        "id": "algebra_complex_numbers",
        "name": "Complex Numbers",
        "category": "Algebra",
        "description": "Add and multiply complex numbers using i^2 = -1.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Multiply (2+3i)(1-2i).",
                    steps=["=2-4i+3i-6i^2", "=2-i+6", "=8-i"],
                    answer="8-i",
                    common_mistakes=["Using i^2 = 1 instead of -1", "FOIL sign errors"],
                ),
            }
        ],
    },
    "algebra_quadratic_functions": {
        "id": "algebra_quadratic_functions",
        "name": "Quadratic Functions and Applications",
        "category": "Algebra",
        "description": "Find vertex, axis of symmetry, and direction of opening for quadratic functions.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find vertex of f(x)=x^2-4x+3.",
                    steps=["x = -b/(2a) = 4/2 = 2", "f(2)=4-8+3=-1", "vertex=(2,-1)"],
                    answer="(2,-1)",
                    common_mistakes=["Sign mistake in -b", "Computing f(2) incorrectly"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="For f(x)=-2x^2+8x+1, find axis and vertex.",
                    steps=["x = -8/(2*-2) = 2", "f(2) = -8+16+1 = 9", "vertex=(2,9)"],
                    answer="axis x=2, vertex (2,9)",
                    common_mistakes=["Losing negative signs", "Wrong substitution into function"],
                ),
            },
        ],
    },
    "algebra_polynomial_division": {
        "id": "algebra_polynomial_division",
        "name": "Division of Polynomials",
        "category": "Algebra",
        "description": "Divide polynomials using long division or synthetic division.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Divide x^3 - 2x^2 + 4 by x - 3.",
                    steps=["quotient = x^2 + x + 3", "remainder = 13"],
                    answer="x^2 + x + 3 with remainder 13",
                    common_mistakes=["Sign errors in synthetic division", "Forgetting remainder term"],
                ),
            }
        ],
    },
    "algebra_remainder_theorem": {
        "id": "algebra_remainder_theorem",
        "name": "Remainder Theorem",
        "category": "Algebra",
        "description": "Use P(c) to find remainder when dividing P(x) by (x-c).",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find remainder when P(x)=x^3-2x^2+4 is divided by x-3.",
                    steps=["remainder = P(3)", "P(3)=27-18+4", "remainder = 13"],
                    answer="13",
                    common_mistakes=["Using wrong c value", "Arithmetic mistakes evaluating P(c)"],
                ),
            }
        ],
    },
    "algebra_factor_theorem": {
        "id": "algebra_factor_theorem",
        "name": "Factor Theorem",
        "category": "Algebra",
        "description": "Determine factors from zeros using P(c)=0.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="If P(2)=0, what does this imply about P(x)?",
                    steps=["P(2)=0 means c=2 is a zero", "(x-2) is a factor"],
                    answer="(x-2) is a factor",
                    common_mistakes=["Using (x+2) instead of (x-2)", "Confusing root and factor signs"],
                ),
            }
        ],
    },
    "algebra_zeros_polynomials": {
        "id": "algebra_zeros_polynomials",
        "name": "Zeros of Polynomials",
        "category": "Algebra",
        "description": "Use rational root theorem and synthetic division to find polynomial zeros.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Find a rational zero of P(x)=x^3-6x^2+11x-6.",
                    steps=["possible roots: ±1, ±2, ±3, ±6", "P(1)=0", "x=1 is a zero"],
                    answer="x=1",
                    common_mistakes=["Listing invalid candidates", "Not testing candidates correctly"],
                ),
            }
        ],
    },
    "algebra_rational_functions": {
        "id": "algebra_rational_functions",
        "name": "Rational Functions",
        "category": "Algebra",
        "description": "Analyze domain, asymptotes, and intercepts of p(x)/q(x).",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="For f(x)=(x+1)/(x-2), find domain and asymptotes.",
                    steps=["domain: x != 2", "vertical asymptote: x=2", "horizontal asymptote: y=1"],
                    answer="domain x!=2, VA x=2, HA y=1",
                    common_mistakes=["Including denominator zeros in domain", "Wrong horizontal asymptote rule"],
                ),
            }
        ],
    },
    "algebra_polynomial_inequalities": {
        "id": "algebra_polynomial_inequalities",
        "name": "Polynomial Inequalities",
        "category": "Algebra",
        "description": "Solve polynomial inequalities using sign charts and interval testing.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve (x-1)(x+2) > 0.",
                    steps=["zeros at x=-2 and x=1", "test intervals", "solution: x<-2 or x>1"],
                    answer="(-inf,-2) U (1,inf)",
                    common_mistakes=["Using roots as included endpoints for strict inequality", "Wrong sign test in intervals"],
                ),
            }
        ],
    },
    "algebra_rational_inequalities": {
        "id": "algebra_rational_inequalities",
        "name": "Rational Inequalities",
        "category": "Algebra",
        "description": "Solve rational inequalities using numerator/denominator sign analysis.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Solve (x-1)/(x+3) >= 0.",
                    steps=["critical points: x=1, x=-3", "test intervals", "solution: x<-3 or x>=1"],
                    answer="(-inf,-3) U [1,inf)",
                    common_mistakes=["Including denominator zero", "Incorrect interval sign chart"],
                ),
            }
        ],
    },
    "algebra_inverse_functions": {
        "id": "algebra_inverse_functions",
        "name": "Inverse Functions",
        "category": "Algebra",
        "description": "Find inverse functions by swapping x and y and solving for y.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Find inverse of f(x)=2x+3.",
                    steps=["y = 2x+3", "x = 2y+3", "y = (x-3)/2"],
                    answer="f^-1(x)=(x-3)/2",
                    common_mistakes=["Forgetting to swap x and y", "Solving incorrectly for y"],
                ),
            }
        ],
    },
    "precalculus_exponential_functions": {
        "id": "precalculus_exponential_functions",
        "name": "Exponential Functions",
        "category": "Precalculus",
        "description": "Analyze growth/decay functions of the form f(x)=a*b^x.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="For f(x)=2*3^x, state growth/decay and y-intercept.",
                    steps=["b=3 > 1 so growth", "f(0)=2*3^0=2"],
                    answer="growth, y-intercept 2",
                    common_mistakes=["Confusing a and b roles", "Incorrectly computing 3^0"],
                ),
            }
        ],
    },
    "precalculus_logarithmic_functions": {
        "id": "precalculus_logarithmic_functions",
        "name": "Logarithmic Functions",
        "category": "Precalculus",
        "description": "Interpret log relationships and inverse relation to exponentials.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Evaluate log base 2 of 8.",
                    steps=["2^y = 8", "y = 3"],
                    answer="3",
                    common_mistakes=["Treating log as division", "Using wrong base"],
                ),
            }
        ],
    },
    "precalculus_log_properties": {
        "id": "precalculus_log_properties",
        "name": "Properties of Logarithms",
        "category": "Precalculus",
        "description": "Apply product, quotient, power, and change-of-base log properties.",
        "available_difficulties": ["beginner", "intermediate", "advanced"],
        "sample_problems": [
            {
                "difficulty": "beginner",
                **_make_sample(
                    problem_statement="Expand log_2(8x).",
                    steps=["log_2(8x)=log_2(8)+log_2(x)", "=3+log_2(x)"],
                    answer="3 + log_2(x)",
                    common_mistakes=["Multiplying logs instead of adding", "Not simplifying log_2(8)"],
                ),
            },
            {
                "difficulty": "intermediate",
                **_make_sample(
                    problem_statement="Rewrite log_5(7) using change of base with natural log.",
                    steps=["log_5(7) = ln(7)/ln(5)"],
                    answer="ln(7)/ln(5)",
                    common_mistakes=["Swapping numerator/denominator", "Using inconsistent bases"],
                ),
            },
        ],
    },
}


def get_all_concepts() -> dict[str, dict[str, object]]:
    # Return a copy so callers don't mutate our source of truth.
    return {cid: dict(details) for cid, details in CONCEPTS.items()}


def get_concept_details(concept_id: str) -> dict[str, Any]:
    if concept_id not in CONCEPTS:
        raise KeyError(f"Unknown concept_id: {concept_id}")

    # Inject prerequisites computed from the prerequisite graph.
    details = dict(CONCEPTS[concept_id])
    details["prerequisites"] = _get_prerequisites(concept_id)
    return details


def get_prerequisites(concept_id: str) -> list[str]:
    return _get_prerequisites(concept_id)


def get_next_concepts(completed_concepts: list[str]) -> list[str]:
    # Phase 1: simple prerequisite-unlock recommendation.
    return _recommend_next_concepts(completed_concepts, k=3)

