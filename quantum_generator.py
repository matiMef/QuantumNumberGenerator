import scipy.stats as stats
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
import secrets
from collections import Counter
# from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
# from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
import matplotlib.pyplot as plt

# Number Generators
# =========================== CSPRNG ==================================
def generate_csprng_numbers(n_qubits: int, n_shots: int) -> list[int]:
    max_val = 2**n_qubits
    return [secrets.randbelow(max_val) for _ in range(n_shots)]
# =========================== CSPRNG ==================================

# =========================== QRNG ====================================
def generate_dynamic_circuit(n_qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits)
    for n in range(n_qubits):
        qc.h(n)
    return qc

def get_results(qc: QuantumCircuit, n_shots: int):
    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=n_shots).result()
    return result

def generate_and_measure(n_qubits: int, n_shots: int) -> list[str]:
    dqc = generate_dynamic_circuit(n_qubits)
    dqc.measure_all()
    results = get_results(dqc, n_shots)
    return results

def bitstrings_to_numbers(results: list[str]) -> list[int]:
    bitstrings = results[0].data.meas.get_bitstrings()
    numbers = [int(b, 2) for b in bitstrings]
    return numbers
# =========================== QRNG ====================================

# =========================== QRNG-IBM ================================
def get_results_from_ibm(qc: QuantumCircuit, n_shots: int, backend_name: str = None):
    service = QiskitRuntimeService(channel="ibm_quantum")
    
    if backend_name:
        backend = service.backend(backend_name)
    else:
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=qc.num_qubits)
    
    print(f"[IBM QPU] Łączenie z fizycznym urządzeniem: {backend.name}")
    
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(qc)
    
    sampler = SamplerV2(backend=backend)
    job = sampler.run([isa_circuit], shots=n_shots)
    print(f"[IBM QPU] Zadanie wysłane! Job ID: {job.job_id()}")
    print("[IBM QPU] Czekam na wykonanie w kolejce...")
    
    result = job.result()
    return result
# =========================== QRNG-IBM ================================

# =========================== Tests =============================
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

def run_test(tests: list[int]):
    all_test_results = []
    
    for test in tests:
        result = generate_and_measure(1, test)
        result_list = bitstrings_to_numbers(result)
        
        if not result_list:
            continue
            
        runs = []
        current_len = 1
        
        for i in range(1, len(result_list)):
            if result_list[i] == result_list[i - 1]:
                current_len += 1
            else:
                runs.append({'number': str(result_list[i - 1]), 'length': current_len})
                current_len = 1
        
        runs.append({'number': str(result_list[-1]), 'length': current_len})
        all_test_results.append(runs)
        
    return all_test_results

def chi_square_test_for_csprng(n_qubits: int, n_shots: int, alpha: float = 0.05):
    numbers = generate_csprng_numbers(n_qubits, n_shots)
    counts = Counter(numbers)
    
    num_states = 2**n_qubits
    observed_counts = [counts.get(i, 0) for i in range(num_states)]

    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    critical_value = stats.chi2.ppf(1 - alpha, num_states - 1)
    
    print(f"--- TEST CHI-KWADRAT CSPRNG ({n_qubits} bitów, shots: {n_shots}) ---")
    print(f"Statystyka Chi2: {chi2_stat:.4f} | p-value: {p_value:.4f}")
    return chi2_stat, p_value

def chi_square_test_for_quantum_rng(n_qubits: int, n_shots: int, alpha: float = 0.05, sim: bool = True, backend_name = "ibm_brisbane"):
    qc = generate_dynamic_circuit(n_qubits)

    if sim:
        qc.measure_all()
        
        res = get_results(qc, n_shots)
    else:
        res = get_results_from_ibm(qc, n_shots, backend_name)

    counts = res[0].data.meas.get_counts()
    num_states = 2**n_qubits
    observed_counts = []
    
    for i in range(num_states):
        bitstring = format(i, f'0{n_qubits}b')
        observed_counts.append(counts.get(bitstring, 0))
    
    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    
    degrees_of_freedom = num_states - 1
    critical_value = stats.chi2.ppf(1 - alpha, degrees_of_freedom)
    
    print(f"--- TEST CHI-KWADRAT DLA {n_qubits} KUBITÓW (Shots: {n_shots}) ---")
    print(f"Liczba możliwych stanów (k): {num_states}")
    print(f"Oczekiwana zliczeń na stan: {expected_count}")
    print(f"Statystyka Chi-kwadrat (chi2_emp): {chi2_stat:.4f}")
    print(f"Wartość krytyczna (alpha={alpha}, df={degrees_of_freedom}): {critical_value:.4f}")
    print(f"p-value: {p_value:.4f}")
    
    if chi2_stat <= critical_value:
        print("\nWniosek: BRAK PODSTAW DO ODRZUCENIA H0.")
        print("Generator kwantowy generuje stany zgodnie z idealnym rozkładem jednostajnym.")
    else:
        print("\nWniosek: ODRZUCAMY H0.")
        print("Generator wykazuje istotne statystycznie odchylenie od rozkładu jednostajnego.")
# =========================== Tests =============================

# =========================== Plots =============================
def plot_statistical_distribution(n_bits: int, shots: int):
    res = generate_and_measure(n_bits, shots)
    counts = res[0].data.meas.get_counts()
    num_states = 2**n_bits
    states = [format(i, f'0{n_bits}b') for i in range(num_states)]
    frequencies = [counts.get(s, 0) for s in states]
    
    plt.figure(figsize=(10, 5))
    plt.bar(states, frequencies, color='skyblue', edgecolor='black')
    plt.xlabel('Stan')
    plt.ylabel('Liczba zliczeń')
    plt.title(f'Rozkład statystyczny QRNG Symulator ({shots} prób, {n_bits} bitów)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('qrng_sim_distribution.png')
    plt.close()

def plot_csprng_distribution(n_bits: int, shots: int):
    numbers = generate_csprng_numbers(n_bits, shots)
    counts = Counter(numbers)
    num_states = 2**n_bits
    states = [format(i, f'0{n_bits}b') for i in range(num_states)]
    frequencies = [counts.get(i, 0) for i in range(num_states)]
    
    plt.figure(figsize=(10, 5))
    plt.bar(states, frequencies, color='salmon', edgecolor='black')
    plt.xlabel('Wartość')
    plt.ylabel('Liczba zliczeń')
    plt.title(f'Rozkład statystyczny CSPRNG ({shots} prób, {n_bits} bitów)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('csprng_distribution.png')
    plt.close()

def plot_runs_test_results(test_shots: int):
    runs_data = run_test([test_shots])[0]
    lengths = [r['length'] for r in runs_data]
    max_len = max(lengths)
    
    plt.figure(figsize=(8, 5))
    plt.hist(lengths, bins=range(1, max_len + 2), align='left', color='lightgreen', edgecolor='black')
    plt.xlabel('Długość serii')
    plt.ylabel('Częstotliwość występowania')
    plt.title(f'Histogram długości serii (Test serii, {test_shots} prób)')
    plt.xticks(range(1, max_len + 1))
    plt.tight_layout()
    plt.savefig('runs_test_histogram.png')
    plt.close()
# =========================== Plots =============================

def main():
    print("Uruchamianie testów i generowanie wykresów...")
    
    chi_square_test_for_quantum_rng(n_qubits=4, n_shots=10000, sim=True)
    chi_square_test_for_csprng(n_qubits=4, n_shots=10000)
    
    statictical_distribution(4, [10000, 100000])
    plot_statistical_distribution(4, 10000)
    plot_csprng_distribution(4, 10000)
    
    print(run_test([1000]))
    plot_runs_test_results(1000)
    
    print("Zakończono pomyślnie.")

if __name__ == "__main__":
    main()
    