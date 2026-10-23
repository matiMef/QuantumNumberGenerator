from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

def generate_dynamic_circuit(n_qubits: int):
    qc = QuantumCircuit(n_qubits)
    for n in range(n_qubits):
        qc.h(n)
    return qc

def get_results(qc: QuantumCircuit, n_shots: int):
    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=n_shots).result()
    return result

def generate_and_measure(n_qubits: int, n_shots: int):
    dqc = generate_dynamic_circuit(n_qubits)
    dqc.measure_all()
    results = get_results(dqc, n_shots)
    return results

def bitstrings_to_numbers(results: list[str]):
    bitstrings = results[0].data.meas.get_bitstrings()
    numbers = [int(b, 2) for b in bitstrings]
    return numbers

def sample_test(n_bits: int, tests: list[int]):
    results = []
    for test in tests:
        result = generate_and_measure(n_bits, test)
        result = result[0].data.meas.get_counts()
        results.append(result)
    return results

def statictical_distribution(n_bits: int, tests: list[int]):
    results = sample_test(n_bits, tests)
    print(results)

# dodać dict dla 0 i 1
def run_test(tests: list[int]):
    results = []
    longest_len = 0
    current_len = 1
    for test in range(tests):
        result = generate_and_measure(1, test[test])
        result = bitstrings_to_numbers(result)
        for number in result:
            if number > 0:
                last = result[number-1]
            else:
                continue

            if result[number] == last:
                current_len += 1
            else:
                if current_len > longest_len:
                    longest_len = current_len
                    current_len = 1

statictical_distribution(4, [1000])