import pylab
import base64, urllib, StringIO

def test_add_to_ten(expect,ans):
  a1=float(ans[0])
  a2=eval(ans[1])
  x = math.sqrt(2)
  y = [x for x in range(10)]
  return (a1+a2)==10

def test_add_to_x(expect, ans, options=10):
  a1=float(ans[0])
  a2=float(ans[1])
  ok = (a1+a2)==int(options if options is not None else 10)
  return dict(ok=ok, msg="options=%s" % options)

def test_plot(expect, ans, options=0):
  xd = pylab.linspace(0,1,100)
  expr = '[ %s for x in xd]' % ans
  try:
    yd = eval(expr)
  except Exception as err:
    msg = "Sorry, cannot evaluate your expression, err=%s" % str(err).replace('<','&lt;')
    return dict(ok=False, msg=msg)
  imgdata = StringIO.StringIO()

  fig = pylab.figure()
  ax = fig.add_subplot(111)
  ax.plot(xd, yd, 'ro')
  ax.plot(xd, yd)
  ax.grid()
  fig.savefig(imgdata, format='png')
  pylab.close()

  imgdata.seek(0)  # rewind the data
  uri = 'data:image/png;base64,' + urllib.quote(base64.b64encode(imgdata.buf))
  msg = '<html><img src = "%s"/>' % uri

  area = sum(yd)/(1.0*len(xd))
  msg += '<p>Area=%s, expected area=%s</p></html>' % (area, options)
  ok = abs(area-float(options))<0.001

  return dict(ok=bool(ok), msg=msg)
