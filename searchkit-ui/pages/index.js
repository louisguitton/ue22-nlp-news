import { withSearchkit } from "@searchkit/client";
import withApollo from "../lib/withApollo";
import dynamic from 'next/dynamic'
import '@elastic/eui/dist/eui_theme_light.css'

const Search = dynamic(
  () => import('../components/Search'),
  { ssr: false }
)


const Index = () => {
  return <Search />
}

export default withApollo(withSearchkit(Index));
