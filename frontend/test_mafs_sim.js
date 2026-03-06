import * as math from 'mathjs';
const compiled = math.compile("n^2");
try {
  console.log(compiled.evaluate({ x: 5 }));
} catch (e) {
  console.error("Error evaluating:", e.message);
}
try {
  console.log(compiled.evaluate({ x: 5, n: 5 }));
} catch (e) {
  console.error("Error evaluating with n:", e.message);
}
