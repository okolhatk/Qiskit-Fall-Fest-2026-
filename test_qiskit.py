from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

# Create a 2-qubit Bell state circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

# Run on a local simulator
sampler = StatevectorSampler()
job = sampler.run([qc], shots=1024)
result = job.result()[0]

print("Measurement counts:", result.data.meas.get_counts())
print(qc.draw())