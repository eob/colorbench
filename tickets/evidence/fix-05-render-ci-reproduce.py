from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[2]
new=(root/'src/matched-render.test.ts').read_text()
old=subprocess.check_output(['git','show','8aac233:src/matched-render.test.ts'],cwd=root,text=True)
def write(name,source):
 d=Path('/tmp')/name;d.mkdir(exist_ok=True)
 if not (d/'node_modules').exists():(d/'node_modules').symlink_to(root/'node_modules',target_is_directory=True)
 for filename in ('prompts.ts','render.ts','types.ts'):source=source.replace(f'"./{filename}"',f'"{root}/src/{filename}"')
 (d/'matched-render.test.ts').write_text(source)
 return d/'matched-render.test.ts'
active=new.replace('for (const html of documents) {','''for (const html of documents) {
        if (pixels.length === 1) {
          console.error("__GC_BOUNDARY__");
          await new Promise(resolve => setTimeout(resolve, 100));
        }''')
active=active.replace('const [output, error, exitCode] = await Promise.all([','''let collections = 0;
  let observed = "";
  const stderr = probe.stderr.pipeThrough(new TransformStream({
    transform(chunk, controller) {
      observed += new TextDecoder().decode(chunk);
      if (!collections && observed.includes("__GC_BOUNDARY__")) { Bun.gc(true); collections += 1; }
      controller.enqueue(chunk);
    },
  }));
  const [output, error, exitCode] = await Promise.all([''').replace('new Response(probe.stderr).text()','new Response(stderr).text()')
active=active.replace('expect(exitCode, error).toBe(0);','console.error(`GC_WHILE_CHILD_BROWSER_ACTIVE=${collections}`);\n  expect(collections).toBe(1);\n  expect(exitCode, error).toBe(0);')
write('colorbench-render-ci-node-active',active)
old=old.replace('await page.setContent(generateHtml(frame(width)));','if (width === 12) { console.error("GC_WHILE_BROWSER_ACTIVE=1"); Bun.gc(true); }\n      await page.setContent(generateHtml(frame(width)));')
write('colorbench-render-ci-reversion',old)
write('colorbench-render-ci-fault',new.replace('canvas[data-region="R"]','canvas[data-region="missing"]'))
write('colorbench-render-ci-timeout',new.replace('const pixels = [];','const pixels = [];\n    await new Promise(() => {});'))
